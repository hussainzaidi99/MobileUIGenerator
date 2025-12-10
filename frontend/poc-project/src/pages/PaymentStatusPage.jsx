import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

// Payment Success Page
export function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [credits, setCredits] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    
    if (sessionId) {
      // Verify payment and fetch updated credits
      verifyPayment(sessionId);
    } else {
      setLoading(false);
    }
  }, [searchParams]);

  const verifyPayment = async (sessionId: string) => {
    try {
      const userId = localStorage.getItem("user_id");
      
      // Fetch updated balance
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );
      
      if (res.ok) {
        const data = await res.json();
        setCredits(data);
      }
    } catch (error) {
      console.error("Failed to verify payment:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-teal-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying payment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-teal-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Success Animation */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-green-500 rounded-full mb-4 animate-bounce">
            <svg
              className="w-12 h-12 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Payment Successful! 🎉
          </h1>
          <p className="text-gray-600">
            Your credits have been added to your account
          </p>
        </div>

        {/* Credits Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          {credits ? (
            <>
              <div className="text-center mb-6">
                <p className="text-sm text-gray-500 mb-2">New Balance</p>
                <p className="text-5xl font-bold text-teal-600 mb-2">
                  {credits.credits.toFixed(2)}
                </p>
                <p className="text-lg text-gray-600">Credits</p>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Tokens Available:</span>
                  <span className="font-semibold text-gray-900">
                    {new Intl.NumberFormat().format(credits.tokens_remaining)}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600">
                Your credits will be available shortly
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate("/")}
            className="w-full py-4 bg-teal-500 hover:bg-teal-600 text-white font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl"
          >
            Start Generating UIs
          </button>
          
          <button
            onClick={() => navigate("/pricing")}
            className="w-full py-4 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-xl transition-all duration-300 border-2 border-gray-200"
          >
            View Pricing Plans
          </button>
        </div>

        {/* Receipt Info */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>A receipt has been sent to your email</p>
          <p className="mt-2">
            Need help?{" "}
            <a href="mailto:support@example.com" className="text-teal-600 hover:underline">
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Cancel Icon */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-yellow-500 rounded-full mb-4">
            <svg
              className="w-12 h-12 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Payment Cancelled
          </h1>
          <p className="text-gray-600">
            You cancelled the payment process
          </p>
        </div>

        {/* Info Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="font-semibold text-gray-900 mb-1">
                  No charges were made
                </p>
                <p className="text-sm text-gray-600">
                  Your payment method was not charged. You can try again anytime.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <svg
                className="w-6 h-6 text-teal-500 flex-shrink-0 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
              </svg>
              <div>
                <p className="font-semibold text-gray-900 mb-1">
                  Need a different plan?
                </p>
                <p className="text-sm text-gray-600">
                  Check out our pricing page to find the perfect plan for your needs.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate("/pricing")}
            className="w-full py-4 bg-teal-500 hover:bg-teal-600 text-white font-semibold rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl"
          >
            Try Again
          </button>
          
          <button
            onClick={() => navigate("/")}
            className="w-full py-4 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-xl transition-all duration-300 border-2 border-gray-200"
          >
            Continue Without Purchase
          </button>
        </div>

        {/* Support */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Questions about pricing?</p>
          <p className="mt-2">
            <a href="mailto:support@example.com" className="text-teal-600 hover:underline">
              Contact our support team
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

// Export both components
export default function PaymentPages() {
  const location = window.location.pathname;
  
  if (location.includes('/success')) {
    return <PaymentSuccess />;
  } else if (location.includes('/cancel')) {
    return <PaymentCancelled />;
  }
  
  return null;
}