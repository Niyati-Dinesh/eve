import React, { useState } from "react";
import aboutVideo2 from "/about_video2.mp4";
import {
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  LogIn,
  UserPlus,
} from "lucide-react";
import toast from "react-hot-toast";
import "./auth.css";

export default function AuthComponent() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Add your authentication logic here
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));
      
      if (isLogin) {
        toast.success("Login successful!");
      } else {
        toast.success("Registration successful!");
      }
    } catch (error) {
      toast.error("Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="authform">
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
          <div className="togglebt">
           
            <button
              className={`loginbt ${isLogin ? "active" : ""}`}
              onClick={() => setIsLogin(true)}
            >
              <LogIn />
              Login
            </button>
            <button
              className={`registerbt ${!isLogin ? "active" : ""}`}
              onClick={() => setIsLogin(false)}
            >
              <UserPlus />
              Register
            </button>
          </div>

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
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
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
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
              )}

              <button
                type="submit"
                className="submit-btn"
                disabled={loading}
              >
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
                <a href="#forgot">Forgot Password?</a>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}