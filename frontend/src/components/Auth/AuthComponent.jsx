import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import aboutVideo2 from "/about_video2.mp4";
import { Mail, Lock, Eye, EyeOff, LogIn, UserPlus, ArrowLeft, KeyRound, ShieldCheck } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";
import "./auth.css";
import { login, register, requestPasswordReset, verifyOTP, resetPassword } from "../../api/auth";
import { useAuth } from "../../context/AuthContext";

// ─── Forgot Password Sub-views ─────────────────────────────────────────────

function ForgotStep1({ onBack, onNext }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await requestPasswordReset(email);
      toast.success("Check your email for the reset code!");
      onNext(email);
    } catch (err) {
      toast.error(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="input-form forgot-form">
      <button type="button" className="back-btn" onClick={onBack}>
        <ArrowLeft size={16} /> Back
      </button>

      <div className="intro">
        <div className="forgot-icon-wrap">
          <KeyRound size={28} color="#FF14A5" />
        </div>
        <h1 className="intro-title">Forgot Password</h1>
        <p className="intro-desc">
          Enter your email and we'll send you a 6-digit code.
        </p>
      </div>

      <div className="fields">
        <div className="field-wrapper">
          <Mail />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email Address"
            required
            autoComplete="email"
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? <span className="spinner" /> : <>Send Reset Code</>}
        </button>
      </div>
    </form>
  );
}

function ForgotStep2({ email, onBack, onNext }) {
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await verifyOTP(email, otp.trim());
      toast.success("Code verified!");
      onNext(data.reset_token);
    } catch (err) {
      toast.error(err.message || "Invalid or expired code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="input-form forgot-form">
      <button type="button" className="back-btn" onClick={onBack}>
        <ArrowLeft size={16} /> Back
      </button>

      <div className="intro">
        <div className="forgot-icon-wrap">
          <ShieldCheck size={28} color="#FF14A5" />
        </div>
        <h1 className="intro-title">Enter Code</h1>
        <p className="intro-desc">
          We sent a 6-digit code to <strong style={{ color: "rgba(255,255,255,0.8)" }}>{email}</strong>
        </p>
      </div>

      <div className="fields">
        <div className="field-wrapper">
          <KeyRound />
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="000000"
            required
            maxLength={6}
            inputMode="numeric"
            autoComplete="one-time-code"
            style={{ letterSpacing: "0.25em", fontSize: "20px", fontWeight: 700 }}
          />
        </div>

        <button type="submit" className="submit-btn" disabled={loading || otp.length < 6}>
          {loading ? <span className="spinner" /> : <>Verify Code</>}
        </button>
      </div>
    </form>
  );
}

function ForgotStep3({ resetToken, onDone }) {
  const [password, setPassword]       = useState("");
  const [confirm, setConfirm]         = useState("");
  const [showPw, setShowPw]           = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading]         = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) return toast.error("Passwords do not match");
    if (password.length < 6)  return toast.error("Password must be at least 6 characters");

    setLoading(true);
    try {
      await resetPassword(resetToken, password);
      toast.success("Password reset! Please sign in.");
      onDone();
    } catch (err) {
      toast.error(err.message || "Reset failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="input-form forgot-form">
      <div className="intro">
        <div className="forgot-icon-wrap">
          <Lock size={28} color="#FF14A5" />
        </div>
        <h1 className="intro-title">New Password</h1>
        <p className="intro-desc">Choose a strong password for your account.</p>
      </div>

      <div className="fields">
        <div className="field-wrapper">
          <Lock />
          <input
            type={showPw ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New Password"
            required
            minLength={6}
            autoComplete="new-password"
          />
          <button type="button" className="password-toggle" onClick={() => setShowPw(!showPw)}>
            {showPw ? <EyeOff /> : <Eye />}
          </button>
        </div>

        <div className="field-wrapper">
          <Lock />
          <input
            type={showConfirm ? "text" : "password"}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Confirm Password"
            required
            minLength={6}
            autoComplete="new-password"
          />
          <button type="button" className="password-toggle" onClick={() => setShowConfirm(!showConfirm)}>
            {showConfirm ? <EyeOff /> : <Eye />}
          </button>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? <span className="spinner" /> : <>Reset Password</>}
        </button>
      </div>
    </form>
  );
}

// ─── Main Auth Component ───────────────────────────────────────────────────

export default function AuthComponent() {
  // "login" | "register" | "forgot-1" | "forgot-2" | "forgot-3"
  const [view, setView]       = useState("login");
  const [forgotEmail, setForgotEmail]       = useState("");
  const [forgotResetToken, setForgotResetToken] = useState("");

  const [showPassword, setShowPassword]           = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: "", password: "", confirmPassword: "" });
  const { setUser } = useAuth();

  const isLogin = view === "login";

  const resetForm = () =>
    setFormData({ email: "", password: "", confirmPassword: "" });

  const handleInputChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setLoading(true);

    if (!isLogin && formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match!");
      setLoading(false);
      return;
    }
    if (!isLogin && formData.password.length < 6) {
      toast.error("Password must be at least 6 characters!");
      setLoading(false);
      return;
    }

    try {
      const data = isLogin
        ? await login(formData.email, formData.password)
        : await register(formData.email, formData.password);

      setUser(data);
      toast.success(isLogin ? "Login successful!" : "Account created!");
      resetForm();
      setTimeout(() => navigate("/dashboard"), 500);
    } catch (err) {
      toast.error(err.message || "Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  // ── Forgot password navigation ────────────────────────────────────────────

  const isForgotView = view.startsWith("forgot");

  const renderRight = () => {
    if (view === "forgot-1")
      return (
        <ForgotStep1
          onBack={() => setView("login")}
          onNext={(email) => { setForgotEmail(email); setView("forgot-2"); }}
        />
      );

    if (view === "forgot-2")
      return (
        <ForgotStep2
          email={forgotEmail}
          onBack={() => setView("forgot-1")}
          onNext={(token) => { setForgotResetToken(token); setView("forgot-3"); }}
        />
      );

    if (view === "forgot-3")
      return (
        <ForgotStep3
          resetToken={forgotResetToken}
          onDone={() => { setView("login"); resetForm(); }}
        />
      );

    // Default: login / register
    return (
      <>
        {/* Toggle */}
        {!isForgotView && (
          <div className="togglebt">
            <button
              type="button"
              className={`loginbt ${isLogin ? "active" : ""}`}
              onClick={() => { setView("login"); resetForm(); }}
            >
              <LogIn /> Login
            </button>
            <button
              type="button"
              className={`registerbt ${!isLogin ? "active" : ""}`}
              onClick={() => { setView("register"); resetForm(); }}
            >
              <UserPlus /> Register
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <div className="intro">
            <h1 className="intro-title">
              {isLogin ? "Welcome Back!" : "Create Account"}
            </h1>
            <p className="intro-desc">
              {isLogin
                ? "Enter your credentials to access your account"
                : "Join the E.V.E. community today"}
            </p>
          </div>

          <div className="fields">
            <div className="field-wrapper">
              <Mail />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Email Address"
                required
                autoComplete="email"
              />
            </div>

            <div className="field-wrapper">
              <Lock />
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Password"
                required
                minLength={6}
                autoComplete={isLogin ? "current-password" : "new-password"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label="Toggle password visibility"
              >
                {showPassword ? <EyeOff /> : <Eye />}
              </button>
            </div>

            {!isLogin && (
              <div className="field-wrapper">
                <Lock />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="Confirm Password"
                  required={!isLogin}
                  minLength={6}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label="Toggle confirm password visibility"
                >
                  {showConfirmPassword ? <EyeOff /> : <Eye />}
                </button>
              </div>
            )}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? (
                <span className="spinner" />
              ) : (
                <>
                  {isLogin ? <LogIn /> : <UserPlus />}
                  {isLogin ? "Sign In" : "Create Account"}
                </>
              )}
            </button>
          </div>

          {isLogin && (
            <div className="forgot-password">
              <button
                type="button"
                className="forgot-link"
                onClick={() => setView("forgot-1")}
              >
                Forgot Password?
              </button>
            </div>
          )}
        </form>
      </>
    );
  };

  return (
    <div id="authform">
      <Toaster position="top-center" />
      <div className="form">
        <div className="left">
          <video
            className="auth-video"
            src={aboutVideo2}
            autoPlay
            playsInline
            muted
            loop
          />
        </div>
        <div className="right">
          {renderRight()}
        </div>
      </div>
    </div>
  );
}