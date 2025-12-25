import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import DarkVeil from "../components/backgrounds/DarkVeil";

export default function PricingPage() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState(null);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);
  const [error, setError] = useState(null);

  // ✅ Use auth context instead of localStorage
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const userId = user?.id;

  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Fetch available packages and balance on mount
  useEffect(() => {
    fetchPackages();
    if (userId) {
      fetchBalance();
    }
  }, [userId]);

  const fetchPackages = async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/packages`
      );

      if (!res.ok) {
        throw new Error("Failed to fetch packages");
      }

      const data = await res.json();
      setPackages(data.packages || []);
    } catch (error) {
      console.error("Failed to fetch packages:", error);
      setError("Failed to load pricing packages. Please refresh the page.");
    } finally {
      setLoading(false);
    }
  };

  const fetchBalance = async () => {
    if (!userId) return;

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );

      if (res.ok) {
        const data = await res.json();
        setBalance(data);
      }
    } catch (error) {
      console.error("Failed to fetch balance:", error);
    }
  };

  const handlePurchase = async (packageId) => {
    if (!userId) {
      alert("Please log in to purchase credits");
      navigate("/auth");
      return;
    }

    setPurchaseLoading(true);
    setSelectedPackage(packageId);

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/create-checkout`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            credits_package: packageId,
          }),
        }
      );

      const data = await res.json();

      if (res.ok && data.url) {
        // Redirect to Stripe Checkout
        window.location.href = data.url;
      } else {
        alert(data.detail || "Failed to create checkout session");
        setPurchaseLoading(false);
        setSelectedPackage(null);
      }
    } catch (error) {
      console.error("Purchase error:", error);
      alert("Something went wrong. Please try again.");
      setPurchaseLoading(false);
      setSelectedPackage(null);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  // ✅ Show login prompt if user is not authenticated
  if (!isAuthenticated) {
    return (
      <div className="pricing-page-container">
        <DarkVeil opacity={isMobile ? 0.25 : 0.4} particleCount={isMobile ? 15 : 40} />
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '80vh',
          position: 'relative',
          zIndex: 10,
          padding: '2rem'
        }}>
          <div style={{
            textAlign: 'center',
            background: 'rgba(30, 41, 59, 0.5)',
            backdropFilter: 'blur(16px)',
            borderRadius: '32px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '4rem 3rem',
            maxWidth: '500px',
            width: '100%',
            animation: 'fadeIn 0.6s ease-out'
          }}>
            <div style={{
              width: '100px',
              height: '100px',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              borderRadius: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 2.5rem',
              fontSize: '3rem',
              boxShadow: '0 20px 40px rgba(99, 102, 241, 0.3)'
            }}>
              🔒
            </div>
            <h2 style={{ fontSize: '2.5rem', fontWeight: '900', color: '#f8fafc', marginBottom: '1rem', letterSpacing: '-0.02em' }}>
              Login Required
            </h2>
            <p style={{ color: '#94a3b8', marginBottom: '3rem', fontSize: '1.25rem', fontWeight: '500' }}>
              Please log in to view pricing and purchase credits
            </p>
            <button
              onClick={() => navigate("/auth")}
              className="btn-purchase primary"
              style={{ width: '100%', fontSize: '1.25rem', padding: '1.25rem' }}
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pricing-page-container">
        <DarkVeil opacity={isMobile ? 0.25 : 0.4} particleCount={isMobile ? 15 : 40} />
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh', position: 'relative', zIndex: 10 }}>
          <div style={{ textAlign: 'center' }}>
            <div className="spinner-large" style={{ margin: '0 auto 2rem' }}></div>
            <p style={{ color: '#f8fafc', fontSize: '1.5rem', fontWeight: '700', letterSpacing: '0.05em' }}>
              Loading Premium Plans...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pricing-page-container">
        <DarkVeil opacity={isMobile ? 0.25 : 0.4} particleCount={isMobile ? 15 : 40} />
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '80vh',
          position: 'relative',
          zIndex: 10,
          padding: '2rem'
        }}>
          <div style={{
            textAlign: 'center',
            background: 'rgba(30, 41, 59, 0.5)',
            backdropFilter: 'blur(16px)',
            borderRadius: '32px',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            padding: '4rem 3rem',
            maxWidth: '500px',
            width: '100%'
          }}>
            <div style={{
              width: '100px',
              height: '100px',
              background: 'linear-gradient(135deg, #ef4444, #dc2626)',
              borderRadius: '30px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 2.5rem',
              fontSize: '3rem',
              boxShadow: '0 20px 40px rgba(239, 68, 68, 0.3)'
            }}>
              ⚠️
            </div>
            <h2 style={{ fontSize: '2.25rem', fontWeight: '900', color: '#f8fafc', marginBottom: '1.5rem' }}>
              Something went wrong
            </h2>
            <p style={{ color: '#94a3b8', marginBottom: '3rem', fontSize: '1.125rem' }}>{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="btn-purchase secondary"
              style={{ width: '100%' }}
            >
              Reload Page
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pricing-page-container">
      <DarkVeil opacity={isMobile ? 0.25 : 0.4} particleCount={isMobile ? 15 : 40} />

      <div style={{ position: 'relative', zIndex: 10 }}>
        {/* Header */}
        <div className="pricing-header">
          <h1>Choose Your Plan</h1>
          <p>1 Credit = 70,000 tokens • Pay only for what you use</p>

          {/* Current Balance */}
          {balance && (
            <div className="balance-card">
              <div className="balance-item">
                <p className="balance-label">Your Balance</p>
                <p className="balance-value">{balance.credits.toFixed(2)} Credits</p>
              </div>
              <div className="balance-divider"></div>
              <div className="balance-item">
                <p className="balance-label">Tokens Remaining</p>
                <p className="balance-value">{formatNumber(balance.tokens_remaining)}</p>
              </div>
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="pricing-cards-grid">
          {packages.map((pkg, index) => {
            const isPopular = pkg.id === "pro";
            const isPurchasing = purchaseLoading && selectedPackage === pkg.id;

            return (
              <div
                key={pkg.id}
                className={`pricing-card ${isPopular ? "popular" : ""}`}
              >
                {/* Popular Badge */}
                {isPopular && (
                  <div className="popular-badge">
                    ⭐ Most Popular
                  </div>
                )}

                {/* Package Icon */}
                <div className="plan-icon">
                  {index === 0 ? "🌱" : index === 1 ? "⚡" : "🚀"}
                </div>

                <h3 className="plan-name">
                  {pkg.name.replace(" Plan", "")}
                </h3>

                <p className="plan-description">
                  {pkg.description.includes(" - ")
                    ? pkg.description.split(" - ")[1]
                    : pkg.description}
                </p>

                {/* Price */}
                <div className="price-container">
                  <div className="price-amount">${pkg.price}</div>
                  <div className="price-label">One-time payment</div>
                </div>

                {/* Features */}
                <div className="features-list">
                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <span className="feature-text">
                      <strong>{pkg.credits}</strong> Credits
                    </span>
                  </div>

                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <span className="feature-text">
                      <strong>{formatNumber(pkg.tokens)}</strong> Tokens
                    </span>
                  </div>

                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <span className="feature-text">
                      ${pkg.price_per_credit.toFixed(4)} per credit
                    </span>
                  </div>

                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <span className="feature-text">Never expires</span>
                  </div>

                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <span className="feature-text">Full access to all features</span>
                  </div>
                </div>

                {/* Purchase Button */}
                <button
                  onClick={() => handlePurchase(pkg.id)}
                  disabled={isPurchasing || purchaseLoading}
                  className={`btn-purchase ${isPopular ? "primary" : "secondary"}`}
                >
                  {isPurchasing ? (
                    <>
                      <span className="spinner"></span>
                      Processing...
                    </>
                  ) : (
                    `Buy ${pkg.credits} Credits`
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Value Proposition */}
        <div className="value-section">
          <h2>Why Choose Our Platform?</h2>
          <div className="value-grid">
            <div className="value-item">
              <div className="value-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3>Lightning Fast</h3>
              <p>
                Generate high-quality UIs in seconds with our optimized AI engine
              </p>
            </div>

            <div className="value-item">
              <div className="value-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <h3>Secure & Private</h3>
              <p>
                Your data is encrypted and we never share it with third parties
              </p>
            </div>

            <div className="value-item">
              <div className="value-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3>Best Value</h3>
              <p>
                Pay only for what you use. Credits expire at the end of the month.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="faq-section">
          <h2>Frequently Asked Questions</h2>

          <details className="faq-item">
            <summary>How do credits work?</summary>
            <p>
              1 credit equals 70,000 tokens. Tokens are used for AI generation
              of your UIs. Your credits can be used anytime, giving you complete
              flexibility.
            </p>
          </details>

          <details className="faq-item">
            <summary>What happens if I run out of credits?</summary>
            <p>
              You'll receive a notification when your credits are running low.
              Simply purchase more credits to continue generating UIs. There's
              no downtime or waiting period.
            </p>
          </details>

          <details className="faq-item">
            <summary>Can I upgrade or change my plan?</summary>
            <p>
              Yes! You can purchase any package at any time. All credits are
              cumulative and added to your existing balance. Mix and match
              packages as needed.
            </p>
          </details>

          <details className="faq-item">
            <summary>Are there any hidden fees?</summary>
            <p>
              Absolutely not! The price you see is the price you pay. No
              subscription fees, no monthly charges, no hidden costs. Just
              simple, transparent pricing.
            </p>
          </details>

          <details className="faq-item">
            <summary>What payment methods do you accept?</summary>
            <p>
              We accept all major credit cards, debit cards, and digital
              payment methods through our secure Stripe integration. Your
              payment information is never stored on our servers.
            </p>
          </details>
        </div>

        {/* Support CTA */}
        <div className="support-cta">
          <h3>Still have questions?</h3>
          <p>Our support team is here to help you</p>
          <a href="mailto:contact@sabasoftgames.com">
            Contact Support
          </a>
        </div>
      </div>
    </div>
  );
}