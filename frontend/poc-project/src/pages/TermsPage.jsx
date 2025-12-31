import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const sections = [
    { id: 'intro', title: 'Introduction', icon: '📝' },
    { id: 'accounts', title: 'User Accounts', icon: '👤' },
    { id: 'ip', title: 'Intellectual Property', icon: '⚖️' },
    { id: 'liability', title: 'Limitation of Liability', icon: '🛡️' },
    { id: 'payments', title: 'Credits & Payments', icon: '💳' },
    { id: 'termination', title: 'Termination', icon: '🚫' },
    { id: 'law', title: 'Governing Law', icon: '🌍' }
];

export default function TermsPage() {
    const navigate = useNavigate();
    const [activeSection, setActiveSection] = useState('intro');
    const [scrollProgress, setScrollProgress] = useState(0);
    const containerRef = useRef(null);

    useEffect(() => {
        const handleScroll = () => {
            const scrollY = window.scrollY;
            const height = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (scrollY / height) * 100;
            setScrollProgress(progress);

            // Simple section detection
            for (const section of sections) {
                const el = document.getElementById(section.id);
                if (el) {
                    const rect = el.getBoundingClientRect();
                    if (rect.top >= 0 && rect.top <= 300) {
                        setActiveSection(section.id);
                    }
                }
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (id) => {
        const element = document.getElementById(id);
        if (element) {
            const headerOffset = 100;
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            background: '#0a0a14',
            color: '#f8fafc',
            paddingBottom: '80px',
            position: 'relative',
            overflow: 'hidden',
            fontFamily: "'Inter', sans-serif"
        }}>
            {/* Scroll Progress Bar */}
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: `${scrollProgress}%`,
                height: '4px',
                background: 'linear-gradient(90deg, #8b5cf6, #ec4899)',
                zIndex: 2000,
                transition: 'width 0.2s ease-out'
            }} />

            {/* Background Decor */}
            <div style={{
                position: 'absolute',
                top: '5%',
                left: '10%',
                width: '600px',
                height: '600px',
                background: 'radial-gradient(circle, rgba(139, 92, 246, 0.08), transparent 70%)',
                filter: 'blur(100px)',
                pointerEvents: 'none'
            }} />
            <div style={{
                position: 'absolute',
                bottom: '15%',
                right: '10%',
                width: '700px',
                height: '700px',
                background: 'radial-gradient(circle, rgba(236, 72, 153, 0.05), transparent 70%)',
                filter: 'blur(100px)',
                pointerEvents: 'none'
            }} />

            <div style={{
                maxWidth: '1200px',
                margin: '0 auto',
                padding: '120px 24px 0',
                display: 'grid',
                gridTemplateColumns: '300px 1fr',
                gap: '64px',
                position: 'relative',
                zIndex: 5
            }}>

                {/* Sidebar Sticky Navigation */}
                <aside style={{
                    position: 'sticky',
                    top: '140px',
                    height: 'fit-content',
                    display: window.innerWidth < 1024 ? 'none' : 'block'
                }}>
                    <div style={{
                        background: 'rgba(20, 20, 35, 0.6)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(139, 92, 246, 0.2)',
                        borderRadius: '24px',
                        padding: '32px',
                        boxShadow: '0 12px 40px rgba(0,0,0,0.3)'
                    }}>
                        <h3 style={{
                            fontSize: '12px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.1em',
                            color: '#94a3b8',
                            marginBottom: '24px',
                            fontWeight: '800'
                        }}>Navigation</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {sections.map(section => (
                                <button
                                    key={section.id}
                                    onClick={() => scrollToSection(section.id)}
                                    style={{
                                        textAlign: 'left',
                                        padding: '12px 16px',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: activeSection === section.id ? '700' : '500',
                                        color: activeSection === section.id ? '#f8fafc' : '#94a3b8',
                                        background: activeSection === section.id ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                                        border: '1px solid',
                                        borderColor: activeSection === section.id ? 'rgba(139, 92, 246, 0.4)' : 'transparent',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px'
                                    }}
                                >
                                    <span style={{ fontSize: '18px' }}>{section.icon}</span>
                                    {section.title}
                                </button>
                            ))}
                        </div>

                        <div style={{
                            marginTop: '40px',
                            padding: '20px',
                            background: 'rgba(139, 92, 246, 0.1)',
                            borderRadius: '16px',
                            border: '1px solid rgba(139, 92, 246, 0.2)'
                        }}>
                            <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.5', margin: 0 }}>
                                Need legal help? <br />
                                <a href="mailto:contact@sabasoftgames.com" style={{ color: '#c084fc', textDecoration: 'none', fontWeight: '700' }}>Contact Support</a>
                            </p>
                        </div>
                    </div>
                </aside>

                {/* Main Content Area */}
                <main style={{ gridColumn: window.innerWidth < 1024 ? '1 / span 2' : '2' }}>

                    <button
                        onClick={() => navigate(-1)}
                        style={{
                            marginBottom: '56px',
                            background: 'rgba(30, 30, 50, 0.6)',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            color: '#cbd5e1',
                            padding: '12px 24px',
                            borderRadius: '14px',
                            cursor: 'pointer',
                            fontSize: '15px',
                            fontWeight: '700',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            backdropFilter: 'blur(10px)',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateX(-5px)';
                            e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)';
                            e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)';
                            e.currentTarget.style.color = '#f8fafc';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateX(0)';
                            e.currentTarget.style.background = 'rgba(30, 30, 50, 0.6)';
                            e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)';
                            e.currentTarget.style.color = '#cbd5e1';
                        }}
                    >
                        ← Returns to Safety
                    </button>

                    <header style={{ marginBottom: '80px' }}>
                        <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '8px 16px',
                            background: 'rgba(16, 185, 129, 0.15)',
                            border: '1px solid rgba(16, 185, 129, 0.4)',
                            borderRadius: '10px',
                            fontSize: '12px',
                            fontWeight: '800',
                            color: '#10b981',
                            marginBottom: '24px',
                            letterSpacing: '0.05em'
                        }}>
                            ✅ LAST UPDATED: DECEMBER 31, 2025
                        </div>
                        <h1 style={{
                            fontSize: window.innerWidth < 768 ? '40px' : '64px',
                            fontWeight: '900',
                            marginBottom: '24px',
                            background: 'linear-gradient(135deg, #f8fafc 0%, #c084fc 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                            lineHeight: '1.1'
                        }}>
                            Terms of Service
                        </h1>
                        <p style={{ fontSize: '20px', color: '#94a3b8', lineHeight: '1.6', maxWidth: '600px' }}>
                            Please read these terms carefully before using AppGen. They define your rights and obligations when using our AI design platform.
                        </p>
                    </header>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
                        {/* 1. Introduction */}
                        <section id="intro" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #8b5cf6, #a855f7)')}>📝</div>
                            <h2 style={sectionTitleStyle}>1. Introduction</h2>
                            <p style={sectionTextStyle}>
                                Welcome to AppGen. These Terms and Conditions govern your use of the AppGen website and services.
                                By accessing or using our platform, you signify that you have read, understood, and agree to be bound by these Terms.
                                If you do not agree, you are not authorized to use the service.
                            </p>
                        </section>

                        {/* 2. User Accounts */}
                        <section id="accounts" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #06b6d4, #0891b2)')}>👤</div>
                            <h2 style={sectionTitleStyle}>2. User Accounts</h2>
                            <p style={sectionTextStyle}>
                                To access full generation features, you must create a secure account.
                                You are responsible for all activity that occurs under your account.
                                Maintain the secrecy of your login credentials. AppGen will not be liable for any loss or damage arising from your failure to protect your account security.
                            </p>
                        </section>

                        {/* 3. Intellectual Property */}
                        <section id="ip" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #10b981, #059669)')}>⚖️</div>
                            <h2 style={sectionTitleStyle}>3. Intellectual Property</h2>
                            <p style={sectionTextStyle}>
                                All technology, algorithms, and UI elements provided by AppGen are protected by copyright and trade secret laws.
                                The software and its source code are our exclusive property.
                                However, UIs generated based on your natural language prompts are your property to use for development purposes, subject to the limitations of our AI models' training data.
                            </p>
                        </section>

                        {/* 4. Limitation of Liability */}
                        <section id="liability" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #f59e0b, #d97706)')}>🛡️</div>
                            <h2 style={sectionTitleStyle}>4. Limitation of Liability</h2>
                            <p style={sectionTextStyle}>
                                AppGen is provided "as is" without warranty of any kind.
                                In no event shall Sabasoft Games or its affiliates be liable for any punitive, special, incidental, indirect, or consequential damages resulting from the use or inability to use the service, even if notified of the possibility of such damage.
                            </p>
                        </section>

                        {/* 5. Credits & Payments */}
                        <section id="payments" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #ec4899, #be185d)')}>💳</div>
                            <h2 style={sectionTitleStyle}>5. Credits & Payments</h2>
                            <p style={sectionTextStyle}>
                                AppGen operates on a credit-based system. Credits are purchased via secure third-party payment processors.
                                Credits are non-refundable once used for generation.
                                Tokens are consumed based on the complexity and volume of the generated code.
                                We reserve the right to change our credit pricing at any time.
                            </p>
                        </section>

                        {/* 6. Termination */}
                        <section id="termination" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #ef4444, #991b1b)')}>🚫</div>
                            <h2 style={sectionTitleStyle}>6. Termination</h2>
                            <p style={sectionTextStyle}>
                                We reserve the right to suspend or terminate your access to the service at our sole discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties, or for any other reason.
                            </p>
                        </section>

                        {/* 7. Governing Law */}
                        <section id="law" style={sectionCardStyle}>
                            <div style={iconHeaderStyle('linear-gradient(135deg, #6366f1, #4338ca)')}>🌍</div>
                            <h2 style={sectionTitleStyle}>7. Governing Law</h2>
                            <p style={sectionTextStyle}>
                                These Terms and your use of the platform shall be governed by and construed in accordance with the laws of the jurisdiction of Sabasoft Games, without regard to conflict of law principles.
                                Any legal action or proceeding related to your access to the platform shall be instituted in the appropriate courts.
                            </p>
                        </section>

                        <div style={{
                            padding: '40px',
                            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1))',
                            borderRadius: '24px',
                            border: '1px solid rgba(139, 92, 246, 0.3)',
                            textAlign: 'center'
                        }}>
                            <h3 style={{ color: '#f8fafc', fontSize: '24px', fontWeight: '800', marginBottom: '16px' }}>Still have questions?</h3>
                            <p style={{ color: '#94a3b8', lineHeight: '1.6', marginBottom: '24px' }}>
                                We're here to help clarify any part of our service agreement.
                            </p>
                            <a
                                href="mailto:contact@sabasoftgames.com"
                                style={{
                                    display: 'inline-block',
                                    padding: '14px 32px',
                                    background: 'linear-gradient(135deg, #8b5cf6, #a855f7)',
                                    color: '#fff',
                                    borderRadius: '12px',
                                    fontWeight: '700',
                                    textDecoration: 'none',
                                    boxShadow: '0 8px 32px rgba(139, 92, 246, 0.4)',
                                    transition: 'transform 0.3s'
                                }}
                                onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
                                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                            >
                                Contact Legal Support
                            </a>
                        </div>
                    </div>
                </main>
            </div>

            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
        
        body { margin: 0; }
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #0a0a14; }
        ::-webkit-scrollbar-thumb { background: #1e1e32; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #8b5cf6; }
      `}</style>
        </div>
    );
}

const sectionCardStyle = {
    background: 'rgba(30, 30, 50, 0.4)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(139, 92, 246, 0.2)',
    borderRadius: '24px',
    padding: '40px',
    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative'
};

const iconHeaderStyle = (gradient) => ({
    width: '56px',
    height: '56px',
    background: gradient,
    borderRadius: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '28px',
    marginBottom: '24px',
    boxShadow: '0 8px 20px rgba(0,0,0,0.3)'
});

const sectionTitleStyle = {
    fontSize: '24px',
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: '16px'
};

const sectionTextStyle = {
    fontSize: '16px',
    color: '#94a3b8',
    lineHeight: '1.7',
    margin: 0
};
