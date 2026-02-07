import { useState } from "react";
import {
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  LogIn,
  UserPlus,
  AlertCircle,
} from "lucide-react";
{/*import axiosInstance from "../api/axiosInstance";*/}
import toast from "react-hot-toast";
import { Navigate, useNavigate } from "react-router-dom";

export default function AuthComponent() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    // Clear error when user starts typing
    if (message) setMessage("");
  };

  const [message, setMessage] = useState("");
  const handleSubmit = async (e) => {
    toast.success("Login successfull!");
  }

  {/*const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    if (!isLogin && formData.password !== formData.confirmPassword) {
      setMessage("Passwords do not match!");
      setLoading(false);
      return;
    }

    try {
      const payload = {
        email: formData.email,
        password: formData.password,
      };

      const response = isLogin
        ? await axiosInstance.post("auth/login", payload)
        : await axiosInstance.post("auth/register", payload);

      if (response.status === 200 || response.status === 201) {
        const { newUser, user, token } = response.data;
        const storedUser = newUser || user;

        sessionStorage.setItem("token", token);
        sessionStorage.setItem("user", JSON.stringify(storedUser));
        sessionStorage.setItem("userEmail", storedUser.email);

        // Trigger navbar update
        window.dispatchEvent(new CustomEvent("authChange"));

       
      }
    } catch (error) {
      let errorMessage = "Something went wrong. Please try again.";

      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.response?.status === 400) {
        errorMessage = isLogin
          ? "Invalid email or password"
          : "Registration failed. Please check your information.";
      } else if (error.response?.status === 404) {
        errorMessage = "Email not found. Please check your email or sign up.";
      } else if (error.response?.status >= 500) {
        errorMessage = "Server error. Please try again later.";
      }

      setMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  */}

  return (
    <>
      <div className="min-h-screen relative overflow-hidden flex items-center justify-center mt-52">
        {/* Auth Form */}
        <div className="relative z-10 w-full max-w-md mx-4">
          <div className="bg-black/40 backdrop-blur-sm border border-white/20 rounded-2xl p-8 shadow-2xl">
            {/* Toggle Buttons */}
            <div className="flex mb-8 bg-white/10 rounded-lg p-1">
              <button
                onClick={() => {
                  setIsLogin(true);
                  setMessage("");
                }}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-300 flex items-center justify-center gap-2 ${
                  isLogin
                    ? "bg-white text-black shadow-lg"
                    : "text-white hover:bg-white/10"
                }`}
              >
                <LogIn className="w-4 h-4" />
                Login
              </button>
              <button
                onClick={() => {
                  setIsLogin(false);
                  setMessage("");
                }}
                className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-300 flex items-center justify-center gap-2 ${
                  !isLogin
                    ? "bg-white text-black shadow-lg"
                    : "text-white hover:bg-white/10"
                }`}
              >
                <UserPlus className="w-4 h-4" />
                Register
              </button>
            </div>

            {/* Form Title */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">
                {isLogin ? "Welcome Back" : "Create Account"}
              </h2>
              <p className="text-white/70 text-sm">
                {isLogin
                  ? "Enter your credentials to access your account"
                  : "Join the CyberTron community today"}
              </p>
            </div>

            {/* Error Message */}
            {message && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400  mt-0.5" />
                <div>
                  <p className="text-red-400 text-sm font-medium">{message}</p>
                  {message.includes("Email not found") && (
                    <button
                      onClick={() => {
                        setIsLogin(false);
                        setMessage("");
                      }}
                      className="text-red-300 hover:text-red-200 text-xs underline mt-1"
                    >
                      Create an account instead
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field */}
              <div className="space-y-2">
                <label className="text-white text-sm font-medium">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-5 h-5" />
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full bg-white/10 border border-white/20 rounded-lg py-3 pl-12 pr-4 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent transition-all duration-300"
                    placeholder="Enter your email"
                    required
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="space-y-2">
                <label className="text-white text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-5 h-5" />
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full bg-white/10 border border-white/20 rounded-lg py-3 pl-12 pr-12 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent transition-all duration-300"
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Confirm Password Field (Register only) */}
              {!isLogin && (
                <div className="space-y-2">
                  <label className="text-white text-sm font-medium">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 w-5 h-5" />
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className={`w-full bg-white/10 border rounded-lg py-3 pl-12 pr-12 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-300 ${
                        formData.confirmPassword &&
                        formData.password !== formData.confirmPassword
                          ? "border-red-500 focus:ring-red-500/50"
                          : "border-white/20 focus:ring-white/50"
                      }`}
                      placeholder="Confirm your password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white/50 hover:text-white transition-colors"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {formData.confirmPassword &&
                    formData.password !== formData.confirmPassword && (
                      <p className="text-red-400 text-xs">
                        Passwords do not match
                      </p>
                    )}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={
                  loading ||
                  (!isLogin && formData.password !== formData.confirmPassword)
                }
                className="w-full bg-white text-black py-3 rounded-lg font-medium hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                ) : (
                  <>
                    {isLogin ? (
                      <LogIn className="w-5 h-5" />
                    ) : (
                      <UserPlus className="w-5 h-5" />
                    )}
                    {isLogin ? "Sign In" : "Create Account"}
                  </>
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-6 text-center">
              <p className="text-white/70 text-sm">
                {isLogin
                  ? "Don't have an account? "
                  : "Already have an account? "}
                <button
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setMessage("");
                  }}
                  className="text-white hover:underline font-medium"
                >
                  {isLogin ? "Sign up" : "Sign in"}
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}