from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import OtpPurpose, User, UserRole
from app.schemas import (
    AuthResponse,
    LoginRequest,
    LoginStartRequest,
    OtpStartResponse,
    OtpVerifyRequest,
    RegisterRequest,
    RegisterStartRequest,
    UpdateProfileRequest,
)
from app.services.email import EmailService
from app.services.otp import OtpService
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
otp_service = OtpService()
email_service = EmailService()


def _auth_response(user: User) -> AuthResponse:
    token = create_access_token(user.id, user.email, user.role)
    return AuthResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        token=token,
        phone=getattr(user, "phone", None),
        company=getattr(user, "company", None),
        job_title=getattr(user, "job_title", None),
        location=getattr(user, "location", None),
        linkedin_url=getattr(user, "linkedin_url", None),
        email_verified=bool(getattr(user, "email_verified", False)),
    )


@router.post("/register/start", response_model=OtpStartResponse)
def register_start(request: RegisterStartRequest, db: Session = Depends(get_db)) -> OtpStartResponse:
    email = request.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    if request.role == UserRole.RECRUITER and not (request.company or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name is required for recruiter registration",
        )

    payload = {
        "email": email,
        "password": request.password,
        "full_name": request.full_name.strip(),
        "role": request.role.value,
        "phone": request.phone.strip(),
        "company": (request.company or "").strip() or None,
        "job_title": (request.job_title or "").strip() or None,
        "location": (request.location or "").strip() or None,
        "linkedin_url": (request.linkedin_url or "").strip() or None,
    }
    otp_service.issue(
        db,
        email=email,
        purpose=OtpPurpose.REGISTER,
        payload=payload,
        subject="Verify your IntelliInterview account",
        body_prefix="Welcome to IntelliInterview. Use this code to verify your email and finish registration.",
    )
    return OtpStartResponse(
        message="Verification code sent. Check your email, or the backend console in development.",
        email=email,
        purpose=OtpPurpose.REGISTER,
        expires_in_minutes=10,
    )


@router.post("/login/start", response_model=OtpStartResponse)
def login_start(request: LoginStartRequest, db: Session = Depends(get_db)) -> OtpStartResponse:
    email = request.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found for this email")

    otp_service.issue(
        db,
        email=email,
        purpose=OtpPurpose.LOGIN,
        payload={"user_id": str(user.id)},
        subject="Your IntelliInterview login code",
        body_prefix="Use this one-time code to sign in to IntelliInterview.",
    )
    return OtpStartResponse(
        message="Login code sent. Check your email, or the backend console in development.",
        email=email,
        purpose=OtpPurpose.LOGIN,
        expires_in_minutes=10,
    )


@router.post("/otp/verify", response_model=AuthResponse)
def verify_otp(request: OtpVerifyRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        challenge = otp_service.verify(
            db,
            email=request.email,
            purpose=request.purpose,
            code=request.otp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if request.purpose == OtpPurpose.REGISTER:
        payload = challenge.payload or {}
        email = str(payload.get("email", request.email)).lower()
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
        user = User(
            email=email,
            password_hash=hash_password(str(payload["password"])),
            full_name=str(payload["full_name"]),
            role=UserRole(payload["role"]),
            phone=payload.get("phone"),
            company=payload.get("company"),
            job_title=payload.get("job_title"),
            location=payload.get("location"),
            linkedin_url=payload.get("linkedin_url"),
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        email_service.send(
            user.email,
            "Welcome to IntelliInterview",
            f"Hi {user.full_name},\n\nYour account is verified. You can now use the IntelliInterview portal.\n",
        )
        return _auth_response(user)

    user = db.query(User).filter(User.email == request.email.lower()).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    user.email_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(user)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Direct register used by automated tests; marks email verified."""
    email = request.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = User(
        email=email,
        password_hash=hash_password(request.password),
        full_name=request.full_name.strip(),
        role=request.role,
        phone=(request.phone or "").strip() or None,
        company=(request.company or "").strip() or None,
        job_title=(request.job_title or "").strip() or None,
        location=(request.location or "").strip() or None,
        linkedin_url=(request.linkedin_url or "").strip() or None,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    email_service.send(
        user.email,
        "Welcome to IntelliInterview",
        f"Hi {user.full_name},\n\nYour IntelliInterview account is ready.\n",
    )
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """Legacy password login kept for compatibility with older clients/tests."""
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _auth_response(user)


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return _auth_response(current_user)


@router.patch("/me", response_model=AuthResponse)
def update_me(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuthResponse:
    current_user.full_name = request.full_name.strip()
    current_user.phone = (request.phone or "").strip() or None
    current_user.company = (request.company or "").strip() or None
    current_user.job_title = (request.job_title or "").strip() or None
    current_user.location = (request.location or "").strip() or None
    current_user.linkedin_url = (request.linkedin_url or "").strip() or None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _auth_response(current_user)
