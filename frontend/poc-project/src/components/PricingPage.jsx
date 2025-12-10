import React, { useState, useEffect } from "react";

// Credit Package Type
interface CreditPackage {
  id: string;
  name: string;
  description: string;
  credits: number;
  tokens: number;
  price: number;
  price_per_credit: number;
}

// User Balance Type
interface UserBalance {
  credits: number;
  tokens_remaining: number;
  last_purchase?: string;
}

export default function PricingPage() {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [balance, setBalance] = useState<UserBalance | null>(null);
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null);
  const [purchaseLoading, setPurchaseLoading] = useState(false);

  // Get user ID from auth context (you'll need to implement this)
  const userId = localStorage.getItem("user_id") || "demo_user";

  // Fetch available packages
  useEffect(() => {
    fetchPackages();
    fetchBalance();
  }, []);

  const fetchPackages = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/payment/packages`);
      const data = await res.json();
      setPackages(data.packages);
    } catch (error) {
      console.error("Failed to fetch packages:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBalance = async () => {
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/payment/balance/${userId}`
      );
      const data = await res.json();
      setBalance(data);
    } catch (error) {
      console.error("Failed to fetch balance:", error);
    }
  };

  const handlePurchase = async (packageId: string) => {
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
        alert("Failed to create checkout session");
      }
    } catch (error) {
      console.error("Purchase error:", error);
      alert("Something went wrong. Please try again.");
    } finally {
      setPurchaseLoading(false);
      setSelectedPackage(null);
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading pricing...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            1 Credit = 70,000 tokens • Pay only for what you use
          </p>

          {/* Current Balance */}
          {balance && (
            <div className="inline-flex items-center gap-4 bg-white rounded-xl shadow-lg px-8 py-4 border-2 border-teal-500">
              <div className="text-left">
                <p className="text-sm text-gray-500">Your Balance</p>
                <p className="text-2xl font-bold text-teal-600">
                  {balance.credits.toFixed(2)} Credits
                </p>
              </div>
              <div className="h-12 w-px bg-gray-300"></div>
              <div className="text-left">
                <p className="text-sm text-gray-500">Tokens Remaining</p>
                <p className="text-lg font-semibold text-gray-700">
                  {formatNumber(balance.tokens_remaining)}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {packages.map((pkg, index) => {
            const isPopular = pkg.id === "pro";
            const isPurchasing = purchaseLoading && selectedPackage === pkg.id;

            return (
              <div
                key={pkg.id}
                className={`relative bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:scale-105 ${
                  isPopular
                    ? "border-4 border-teal-500 transform scale-105"
                    : "border-2 border-gray-200"
                }`}
              >
                {/* Popular Badge */}
                {isPopular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-teal-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Package Icon */}
                <div className="text-center mb-6">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-teal-400 to-teal-600 rounded-xl flex items-center justify-center text-3xl">
                    {index === 0 ? "🌱" : index === 1 ? "⚡" : "🚀"}
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900">
                    {pkg.name.replace(" Plan", "")}
                  </h3>
                  <p className="text-gray-500 text-sm mt-2">
                    {pkg.description.split(" - ")[1]}
                  </p>
                </div>

                {/* Price */}
                <div className="text-center mb-6">
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-5xl font-bold text-gray-900">
                      ${pkg.price}
                    </span>
                    <span className="text-gray-500">/month</span>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-4 mb-8">
                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-teal-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">
                      <strong>{pkg.credits}</strong> Credits
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-teal-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">
                      <strong>{formatNumber(pkg.tokens)}</strong> Tokens
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-teal-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">
                      ${pkg.price_per_credit.toFixed(4)}/credit
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-teal-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">Valid for 30 days</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <svg
                      className="w-5 h-5 text-teal-500 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">No expiration</span>
                  </div>
                </div>

                {/* Purchase Button */}
                <button
                  onClick={() => handlePurchase(pkg.id)}
                  disabled={isPurchasing}
                  className={`w-full py-4 rounded-xl font-semibold text-lg transition-all duration-300 ${
                    isPopular
                      ? "bg-teal-500 hover:bg-teal-600 text-white shadow-lg hover:shadow-xl"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-900"
                  } ${isPurchasing ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {isPurchasing ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Processing...
                    </span>
                  ) : (
                    `Buy ${pkg.credits} Credits`
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-16 max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <details className="bg-white rounded-lg p-6 shadow">
              <summary className="font-semibold cursor-pointer">
                How do credits work?
              </summary>
              <p className="mt-2 text-gray-600">
                1 credit = 70,000 tokens. Tokens are used for AI generation.
                Your credits never expire and can be used anytime.
              </p>
            </details>

            <details className="bg-white rounded-lg p-6 shadow">
              <summary className="font-semibold cursor-pointer">
                What happens if I run out of credits?
              </summary>
              <p className="mt-2 text-gray-600">
                You'll be notified when your credits are low. Simply purchase
                more credits to continue generating UIs.
              </p>
            </details>

            <details className="bg-white rounded-lg p-6 shadow">
              <summary className="font-semibold cursor-pointer">
                Can I upgrade or downgrade my plan?
              </summary>
              <p className="mt-2 text-gray-600">
                Yes! You can purchase any package at any time. Credits are
                cumulative and never expire.
              </p>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}