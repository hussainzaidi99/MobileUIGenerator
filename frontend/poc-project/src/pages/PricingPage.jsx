import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import DarkVeil from "../components/backgrounds/DarkVeil";
import { toast } from '../utils/toast';

export default function PricingPage() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    fetchPackages();
    if (userId) {
      fetchBalance();
    }
  }, [userId]);

  const fetchPackages = async () => {
    // Original packages from backend/Services/tier_manager.py
    const fallbackPackages = [
      {
        id: "basic",
        name: "Basic Plan",
        description: "142 Credits - Perfect for small projects (30 days)",
        credits: 142,
        tokens: 10000000,
        price: 4.99,
        price_per_credit: 4.99 / 142,
        duration_days: 30,
        features: ["142 credits/month", "10M tokens", "Email support", "Priority generation"]
      },
      {
        id: "pro",
        name: "Pro Plan",
        description: "284 Credits - Great for regular use (30 days)",
        credits: 284,
        tokens: 20000000,
        price: 9.99,
        price_per_credit: 9.99 / 284,
        duration_days: 30,
        features: ["284 credits/month", "20M tokens", "Email support", "Priority generation", "Advanced components"]
      },
      {
        id: "premium",
        name: "Premium Plan",
        description: "568 Credits - Best value for power users (30 days)",
        credits: 568,
        tokens: 40000000,
        price: 19.99,
        price_per_credit: 19.99 / 568,
        duration_days: 30,
        features: ["568 credits/month", "40M tokens", "Priority support", "Advanced features", "Custom components"]
      }
    ];

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/packages`
      );

      if (!res.ok) {
        throw new Error("Failed to fetch packages");
      }

      const data = await res.json();
      setPackages(data.packages && data.packages.length > 0 ? data.packages : fallbackPackages);
    } catch (error) {
      console.error("Failed to fetch packages, using fallbacks:", error);
      setPackages(fallbackPackages);
      // We don't set a critical error here so users can still see the fallbacks
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
      toast.info("Login Required", "Please log in to purchase credits");
      navigate("/auth", { state: { from: { pathname: '/pricing' } } });
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
        window.location.href = data.url;
      } else {
        throw new Error(data.error || data.detail || "Failed to create checkout session");
      }
    } catch (err) {
      console.error("Purchase error:", err);
      toast.error("Checkout Failed", err.message || "Something went wrong.");
    } finally {
      setPurchaseLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return "0";
    return new Intl.NumberFormat().format(num);
  };

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0f172a'
      }}>
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f172a",
      color: "#f8fafc",
      padding: "120px 24px 80px",
      position: "relative",
      overflow: "hidden"
    }}>
      {/* Background Decor */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '5%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(139, 92, 246, 0.1), transparent 70%)',
        filter: 'blur(80px)',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '10%',
        right: '5%',
        width: '500px',
        height: '500px',
        background: 'radial-gradient(circle, rgba(6, 182, 212, 0.08), transparent 70%)',
        filter: 'blur(80px)',
        pointerEvents: 'none'
      }} />

      <div style={{ maxWidth: "1200px", margin: "0 auto", position: "relative", zIndex: 2 }}>

        {/* Header Section */}
        <div style={{ textAlign: "center", marginBottom: "80px" }}>
          <div style={{
            display: 'inline-block',
            padding: '8px 20px',
            background: 'rgba(139, 92, 246, 0.2)',
            border: '1px solid rgba(139, 92, 246, 0.4)',
            borderRadius: '20px',
            fontSize: '14px',
            fontWeight: '700',
            color: '#c084fc',
            marginBottom: '24px'
          }}>
            💎 PREMIUM ACCESS
          </div>
          <h1 style={{
            fontSize: isMobile ? "40px" : "64px",
            fontWeight: "900",
            marginBottom: "24px",
            background: "linear-gradient(135deg, #f8fafc 0%, #c084fc 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            lineHeight: "1.1"
          }}>
            Simple, Transparent Pricing
          </h1>
          <p style={{
            fontSize: "20px",
            color: "#94a3b8",
            maxWidth: "700px",
            margin: "0 auto",
            lineHeight: "1.6"
          }}>
            No subscriptions. No hidden fees. Pay only for what you need to build your dream mobile interfaces.
          </p>

          {balance && (
            <div style={{
              marginTop: '40px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '24px',
              padding: '16px 32px',
              background: 'rgba(30, 30, 50, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '16px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}>
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Current Balance</div>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#f8fafc' }}>
                  💳 {formatNumber(balance.credits)} Credits
                </div>
              </div>
              <div style={{ width: '1px', height: '40px', background: 'rgba(139, 92, 246, 0.2)' }} />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Token Equivalent</div>
                <div style={{ fontSize: '24px', fontWeight: '800', color: '#c084fc' }}>
                  ✨ {formatNumber(balance.tokens_remaining || balance.tokens || 0)} Tokens
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Packages Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(350px, 1fr))",
          gap: "32px",
          marginBottom: "80px"
        }}>
          {packages.map((pkg) => {
            const isPopular = pkg.id === "pro" || pkg.credits === 284;
            return (
              <div
                key={pkg.id}
                style={{
                  background: 'rgba(30, 30, 50, 0.4)',
                  backdropFilter: 'blur(20px)',
                  border: isPopular ? '2px solid #8b5cf6' : '1px solid rgba(139, 92, 246, 0.2)',
                  borderRadius: '24px',
                  padding: '48px 40px',
                  position: 'relative',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  display: 'flex',
                  flexDirection: 'column',
                  transform: isPopular ? 'scale(1.05)' : 'scale(1)',
                  zIndex: isPopular ? 10 : 1
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = isPopular ? 'scale(1.08) translateY(-8px)' : 'scale(1.03) translateY(-8px)';
                  e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.6)';
                  e.currentTarget.style.boxShadow = '0 20px 60px rgba(139, 92, 246, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = isPopular ? 'scale(1.05)' : 'scale(1)';
                  e.currentTarget.style.borderColor = isPopular ? '#8b5cf6' : 'rgba(139, 92, 246, 0.2)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {isPopular && (
                  <div style={{
                    position: 'absolute',
                    top: '-16px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                    color: '#fff',
                    padding: '6px 20px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: '800',
                    boxShadow: '0 4px 12px rgba(139, 92, 246, 0.4)',
                    letterSpacing: '0.05em'
                  }}>
                    MOST POPULAR
                  </div>
                )}

                <h3 style={{ fontSize: '28px', fontWeight: '800', color: '#f8fafc', marginBottom: '12px' }}>
                  {pkg.name.replace(" Plan", "")}
                </h3>
                <p style={{ fontSize: '16px', color: '#94a3b8', lineHeight: '1.6', marginBottom: '32px' }}>
                  {pkg.description ? (pkg.description.includes(" - ") ? pkg.description.split(" - ")[1] : pkg.description) : "Premium UI Generation Plan"}
                </p>

                <div style={{ marginBottom: '32px' }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontSize: '48px', fontWeight: '900', color: '#f8fafc' }}>${pkg.price}</span>
                    <span style={{ fontSize: '16px', color: '#64748b' }}>one-time</span>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '40px', flex: 1 }}>
                  {[
                    { icon: '💳', text: <strong>{pkg.credits} Credits</strong> },
                    { icon: '✨', text: <span><strong>{formatNumber(pkg.tokens || pkg.credits * 70000)}</strong> Tokens</span> },
                    { icon: '💰', text: <span>${(pkg.price_per_credit || (pkg.price / pkg.credits) || 0).toFixed(4)} per credit</span> },
                    { icon: '🚀', text: 'Full access to all features' },
                    { icon: '📱', text: 'Unlimited Exports' }
                  ].map((feature, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '15px' }}>
                      <span style={{ fontSize: '18px' }}>{feature.icon}</span>
                      <span style={{ color: '#cbd5e1' }}>{feature.text}</span>
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => handlePurchase(pkg.id)}
                  disabled={purchaseLoading && selectedPackage === pkg.id}
                  style={{
                    width: '100%',
                    padding: '16px',
                    borderRadius: '16px',
                    fontSize: '16px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    background: isPopular
                      ? 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)'
                      : 'rgba(30, 30, 50, 0.6)',
                    border: isPopular ? 'none' : '1px solid rgba(139, 92, 246, 0.4)',
                    color: '#FFFFFF',
                    boxShadow: isPopular ? '0 8px 32px rgba(139, 92, 246, 0.4)' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    if (isPopular) {
                      e.currentTarget.style.boxShadow = '0 12px 40px rgba(139, 92, 246, 0.6)';
                    } else {
                      e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
                      e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.6)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    if (isPopular) {
                      e.currentTarget.style.boxShadow = '0 8px 32px rgba(139, 92, 246, 0.4)';
                    } else {
                      e.currentTarget.style.background = 'rgba(30, 30, 50, 0.6)';
                      e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.4)';
                    }
                  }}
                >
                  {purchaseLoading && selectedPackage === pkg.id ? (
                    'Processing...'
                  ) : (
                    <>Buy {pkg.credits} Credits</>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Why Us Section */}
        <div style={{
          textAlign: "center",
          marginBottom: "100px",
          padding: "80px 40px",
          background: "rgba(30, 30, 50, 0.4)",
          backdropFilter: "blur(20px)",
          borderRadius: "32px",
          border: "1px solid rgba(139, 92, 246, 0.2)"
        }}>
          <h2 style={{ fontSize: "36px", fontWeight: "900", marginBottom: "48px", color: "#f8fafc" }}>Why Choose AppGen?</h2>
          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(3, 1fr)", gap: "40px" }}>
            {[
              { title: "Lightning Fast", desc: "Generate high-quality UIs in seconds with our optimized AI engine", icon: "⚡" },
              { title: "Secure & Private", desc: "Your data is encrypted and we never share it with third parties", icon: "🛡️" },
              { title: "Best Value", desc: "Pay only for what you use. No ongoing subscriptions or hidden costs.", icon: "💎" }
            ].map((item, i) => (
              <div key={i}>
                <div style={{ fontSize: "40px", marginBottom: "20px" }}>{item.icon}</div>
                <h3 style={{ fontSize: "20px", fontWeight: "700", marginBottom: "12px", color: "#f8fafc" }}>{item.title}</h3>
                <p style={{ color: "#94a3b8", lineHeight: "1.6" }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ Section */}
        <div style={{ maxWidth: "800px", margin: "0 auto", marginBottom: "80px" }}>
          <h2 style={{ fontSize: "36px", fontWeight: "900", textAlign: "center", marginBottom: "48px", color: "#f8fafc" }}>FAQ</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {[
              { q: "How do credits work?", a: "1 credit equals roughly 70,000 tokens. Tokens are used for AI generation of your UIs. Your credits never expire as long as your account is active." },
              { q: "What happens if I run out?", a: "Simply purchase more credits to continue generating UIs. There's no downtime or waiting period." },
              { q: "Is it a subscription?", a: "No, we use a pay-as-you-go model. You buy credits only when you need them." }
            ].map((faq, i) => (
              <details key={i} style={{
                background: "rgba(30, 30, 50, 0.4)",
                borderRadius: "16px",
                border: "1px solid rgba(139, 92, 246, 0.1)",
                overflow: "hidden"
              }}>
                <summary style={{
                  padding: "20px 24px",
                  cursor: "pointer",
                  fontWeight: "700",
                  color: "#f8fafc",
                  listStyle: "none",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}>
                  {faq.q}
                  <span style={{ color: "#8b5cf6" }}>▼</span>
                </summary>
                <div style={{ padding: "0 24px 20px", color: "#94a3b8", lineHeight: "1.6" }}>
                  {faq.a}
                </div>
              </details>
            ))}
          </div>
        </div>

        {/* Support CTA */}
        <div style={{
          textAlign: "center",
          padding: "60px",
          borderRadius: "24px",
          background: "linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)",
          border: "1px solid rgba(139, 92, 246, 0.2)"
        }}>
          <h3 style={{ fontSize: "24px", fontWeight: "800", marginBottom: "12px", color: "#f8fafc" }}>Still have questions?</h3>
          <p style={{ color: "#94a3b8", marginBottom: "24px" }}>Our support team is here to help you</p>
          <a
            href="mailto:contact@sabasoftgames.com"
            style={{
              display: "inline-block",
              padding: "12px 32px",
              background: "#8b5cf6",
              color: "#fff",
              borderRadius: "12px",
              textDecoration: "none",
              fontWeight: "700",
              transition: "all 0.3s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.05)"}
            onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
          >
            Contact Support
          </a>
        </div>

      </div>

      <style>{`
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid rgba(139, 92, 246, 0.2);
          borderTopColor: #8b5cf6;
          borderRightColor: #8b5cf6;
          borderBottomColor: #8b5cf6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        details > summary::-webkit-details-marker {
          display: none;
        }
      `}</style>
    </div>
  );
}