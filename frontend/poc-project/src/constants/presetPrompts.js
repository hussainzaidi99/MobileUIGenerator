// frontend/src/constants/presetPrompts.js

export const PRESET_PROMPTS = [
  {
    id: 'auth-modern',
    category: 'Authentication',
    label: 'Modern Login & Signup',
    prompt: 'Modern mobile authentication screens with email/password login, social login (Google, Apple), signup form with name and email, forgot password link, and elegant teal gradient buttons with card-based layout',
    icon: '🔐',
  },
  {
    id: 'ecommerce-shop',
    category: 'E-commerce',
    label: 'Product Shopping App',
    prompt: 'Modern e-commerce app with rounded search bar, 2-column product grid showing images, titles, prices, ratings, and sale badges, Add to Cart buttons with orange gradient, and floating cart button in bottom-right corner',
    icon: '🛍️',
  },
  {
    id: 'ecommerce-cart',
    category: 'E-commerce',
    label: 'Shopping Cart & Checkout',
    prompt: 'Shopping cart screen with product thumbnails, quantity controls, remove buttons, price breakdown (subtotal, shipping, tax, total), and prominent Checkout button with orange gradient',
    icon: '🛒',
  },
  {
    id: 'social-feed',
    category: 'Social',
    label: 'Social Media Feed',
    prompt: 'Social media feed with user avatars, post cards showing images, like/comment/share buttons, infinite scroll layout, floating action button for creating posts, and bottom navigation tabs',
    icon: '📱',
  },
  {
    id: 'social-profile',
    category: 'Social',
    label: 'User Profile',
    prompt: 'User profile screen with cover photo, large centered avatar, follower/following/posts stats in 3-column grid, Follow and Message buttons, and photo gallery grid showing user posts',
    icon: '👤',
  },
  {
    id: 'dashboard-analytics',
    category: 'Dashboard',
    label: 'Analytics Dashboard',
    prompt: 'Analytics dashboard with 2x2 grid of stat cards showing revenue, users, growth, and conversion metrics with icons, progress bars for monthly goals, and recent activity list',
    icon: '📊',
  },
  {
    id: 'dashboard-fitness',
    category: 'Dashboard',
    label: 'Fitness Tracker',
    prompt: 'Fitness dashboard showing daily stats (calories, steps, water, sleep) in colorful stat cards, weekly progress bars, and Log Workout button with blue gradient',
    icon: '💪',
  },
  {
    id: 'onboarding-3step',
    category: 'Onboarding',
    label: '3-Step Welcome Flow',
    prompt: 'Multi-step onboarding with large illustrations, progress bar showing 3 steps, centered titles and descriptions, Continue button with blue gradient, and Skip option',
    icon: '👋',
  },
  {
    id: 'settings-menu',
    category: 'Settings',
    label: 'Settings & Preferences',
    prompt: 'Settings screen with grouped sections (Account, Preferences, Support), list items with icons and chevron indicators, toggle switches for notifications and dark mode, and Sign Out option',
    icon: '⚙️',
  },
  {
    id: 'settings-profile-edit',
    category: 'Settings',
    label: 'Edit Profile Form',
    prompt: 'Edit profile screen with large centered avatar, Change Photo link, input fields for name/email/phone/bio with icons, Save Changes button with teal gradient, and Cancel option',
    icon: '✏️',
  },
];

export const PRESET_CATEGORIES = [
  'Authentication',
  'E-commerce',
  'Social',
  'Dashboard',
  'Onboarding',
  'Settings',
];

export const getPresetsByCategory = (category) => {
  return PRESET_PROMPTS.filter(p => p.category === category);
};

export const getPresetById = (id) => {
  return PRESET_PROMPTS.find(p => p.id === id);
};