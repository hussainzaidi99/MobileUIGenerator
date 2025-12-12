import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

// Payment Success Page
export function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [credits, setCredits] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    
    if (sessionId) {
      verifyPayment(sessionId);
    } else {
      setLoading(false);
    }
  }, [searchParams]);

  const verifyPayment = async (sessionId) => {
    try {
      const userId = sessionStorage.getItem("auth_user");
      const user = userId ? JSON.parse(userId) : null;
      
      if (!user?.id) {
        setError("User not authenticated");
        setLoading(false);
        return;
      }

      // Verify payment with backend
      const verifyRes = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/verify-session`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            user_id: user.id
          })
        }
      );

      if (!verifyRes.ok) {
        throw new Error("Payment verification failed");
      }

      // Fetch updated balance
      const balanceRes = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${user.id}`
      );
      
      if (balanceRes.ok) {
        const data = await balanceRes.json();
        setCredits(data);
      }
    } catch (error) {
      console.error("Failed to verify payment:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="payment-status-container">
        <div className="payment-status-card">
          <div className="loading-spinner"></div>
          <p className="status-text">Verifying payment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="payment-status-container">
        <div className="payment-status-card">
          <div className="status-icon error-icon">⚠️</div>
          <h1 className="status-title">Verification Error</h1>
          <p className="status-message">{error}</p>
          <button onClick={() => navigate("/pricing")} className="status-button primary">
            Back to Pricing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-status-container success-bg">
      <div className="payment-status-card success-card">
        {/* Animated Success Icon */}
        <div className="status-icon-wrapper">
          <div className="success-checkmark">
            <div className="check-icon">
              <span className="icon-line line-tip"></span>
              <span className="icon-line line-long"></span>
              <div className="icon-circle"></div>
              <div className="icon-fix"></div>
            </div>
          </div>
        </div>

        {/* Header */}
        <h1 className="status-title success-title">Payment Successful! 🎉</h1>
        <p className="status-subtitle">Your credits have been added to your account</p>

        {/* Credits Card */}
        {credits ? (
          <div className="credits-display-card">
            <div className="credits-main">
              <div className="credits-label">New Balance</div>
              <div className="credits-amount">{credits.credits.toFixed(2)}</div>
              <div className="credits-text">Credits</div>
            </div>

            <div className="credits-divider"></div>

            <div className="credits-secondary">
              <div className="credits-detail">
                <span className="detail-label">Tokens Available:</span>
                <span className="detail-value">
                  {new Intl.NumberFormat().format(credits.tokens_remaining)}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="credits-display-card">
            <p className="credits-pending">Your credits will be available shortly</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="status-actions">
          <button
            onClick={() => navigate("/app")}
            className="status-button primary large"
          >
            <span>Start Generating UIs</span>
            <span className="button-arrow">→</span>
          </button>
          
          <button
            onClick={() => navigate("/pricing")}
            className="status-button secondary"
          >
            View Pricing Plans
          </button>
        </div>

        {/* Receipt Info */}
        <div className="receipt-info">
          <div className="receipt-icon">📧</div>
          <p>A receipt has been sent to your email</p>
          <p className="support-text">
            Need help?{" "}
            <a href="mailto:support@example.com" className="support-link">
              Contact Support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

// Payment Cancelled Page
export function PaymentCancelled() {
  const navigate = useNavigate();

  return (
    <div className="payment-status-container cancelled-bg">
      <div className="payment-status-card cancelled-card">
        {/* Cancel Icon */}
        <div className="status-icon-wrapper">
          <div className="cancel-icon-circle">
            <div className="cancel-x">
              <span className="x-line x-line-1"></span>
              <span className="x-line x-line-2"></span>
            </div>
          </div>
        </div>

        {/* Header */}
        <h1 className="status-title">Payment Cancelled</h1>
        <p className="status-subtitle">You cancelled the payment process</p>

        {/* Info Cards */}
        <div className="info-cards">
          <div className="info-card">
            <div className="info-icon blue">ℹ️</div>
            <div className="info-content">
              <h3 className="info-title">No charges were made</h3>
              <p className="info-text">
                Your payment method was not charged. You can try again anytime.
              </p>
            </div>
          </div>

          <div className="info-card">
            <div className="info-icon teal">💡</div>
            <div className="info-content">
              <h3 className="info-title">Need a different plan?</h3>
              <p className="info-text">
                Check out our pricing page to find the perfect plan for your needs.
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="status-actions">
          <button
            onClick={() => navigate("/pricing")}
            className="status-button primary large"
          >
            <span>Try Again</span>
            <span className="button-arrow">→</span>
          </button>
          
          <button
            onClick={() => navigate("/")}
            className="status-button secondary"
          >
            Continue Without Purchase
          </button>
        </div>

        {/* Support Info */}
        <div className="receipt-info">
          <p className="support-text">
            Questions about pricing?{" "}
            <a href="mailto:support@example.com" className="support-link">
              Contact our support team
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function PaymentPages() {
  const location = window.location.pathname;
  
  if (location.includes('/success')) {
    return <PaymentSuccess />;
  } else if (location.includes('/cancel')) {
    return <PaymentCancelled />;
  }
  
  return null;
}