// src/utils/pexelsClient.js
// Pexels API Client for Dynamic Image Fetching

const PEXELS_API_KEY = import.meta.env.VITE_PEXELS_API_KEY;
const PEXELS_API_BASE = 'https://api.pexels.com/v1';

// In-memory cache to avoid redundant API calls
const imageCache = new Map();

/**
 * Search for photos on Pexels based on a query
 * @param {string} query - Search query (e.g., "coffee", "nature", "technology")
 * @param {object} options - Additional options
 * @param {number} options.perPage - Number of results per page (default: 15)
 * @param {string} options.orientation - Image orientation: 'landscape', 'portrait', 'square'
 * @returns {Promise<string|null>} - URL of a matching image or null
 */
export async function searchPexelsPhoto(query, options = {}) {
    if (!PEXELS_API_KEY) {
        console.warn('⚠️ VITE_PEXELS_API_KEY not found in environment variables');
        return null;
    }

    if (!query || typeof query !== 'string') {
        console.warn('⚠️ Invalid query provided to Pexels search');
        return null;
    }

    // Normalize query for caching
    const normalizedQuery = query.toLowerCase().trim();
    const { perPage = 15, orientation = 'landscape' } = options;
    const cacheKey = `${normalizedQuery}-${orientation}`;

    // Check cache first for a list of photos
    if (imageCache.has(cacheKey)) {
        const cacheEntry = imageCache.get(cacheKey);
        const { photos, nextIndex } = cacheEntry;

        if (photos && photos.length > 0) {
            // Pick next photo in cycle for uniqueness
            const currentIndex = nextIndex % photos.length;
            const photo = photos[currentIndex];
            cacheEntry.nextIndex = currentIndex + 1;

            const imageUrl = photo.src.large;
            console.log(`✅ Using unique cached Pexels image (${currentIndex + 1}/${photos.length}) for: "${query}"`);
            return imageUrl;
        }
    }

    try {
        const url = new URL(`${PEXELS_API_BASE}/search`);
        url.searchParams.set('query', normalizedQuery);
        url.searchParams.set('per_page', perPage);
        if (orientation) {
            url.searchParams.set('orientation', orientation);
        }

        console.log(`🔍 Fetching Pexels images for: "${query}"`);

        const response = await fetch(url.toString(), {
            headers: {
                'Authorization': PEXELS_API_KEY,
            },
        });

        if (!response.ok) {
            console.error(`❌ Pexels API error: ${response.status} ${response.statusText}`);
            return null;
        }

        const data = await response.json();

        if (!data.photos || data.photos.length === 0) {
            console.warn(`⚠️ No Pexels images found for: "${query}"`);
            return null;
        }

        // Store entire list in cache with an iterator index
        imageCache.set(cacheKey, {
            photos: data.photos,
            nextIndex: 1 // Next call will use index 1
        });

        const imageUrl = data.photos[0].src.large;
        console.log(`✅ Pexels image fetched (1/${data.photos.length}): ${imageUrl.substring(0, 60)}...`);
        return imageUrl;

    } catch (error) {
        console.error('❌ Pexels fetch error:', error);
        return null;
    }
}

/**
 * Get a curated photo from Pexels (trending/popular images)
 * @param {number} page - Page number (default: 1)
 * @returns {Promise<string|null>} - URL of a curated image or null
 */
export async function getCuratedPexelsPhoto(page = 1) {
    if (!PEXELS_API_KEY) {
        console.warn('⚠️ VITE_PEXELS_API_KEY not found in environment variables');
        return null;
    }

    try {
        const url = `${PEXELS_API_BASE}/curated?page=${page}&per_page=15`;

        const response = await fetch(url, {
            headers: {
                'Authorization': PEXELS_API_KEY,
            },
        });

        if (!response.ok) {
            console.error(`❌ Pexels API error: ${response.status} ${response.statusText}`);
            return null;
        }

        const data = await response.json();

        if (!data.photos || data.photos.length === 0) {
            return null;
        }

        // Get a random curated photo
        const randomIndex = Math.floor(Math.random() * data.photos.length);
        const photo = data.photos[randomIndex];

        return photo.src.large;

    } catch (error) {
        console.error('❌ Pexels curated fetch error:', error);
        return null;
    }
}

/**
 * Clear the image cache (useful for testing or memory management)
 */
export function clearPexelsCache() {
    imageCache.clear();
    console.log('🗑️ Pexels image cache cleared');
}

/**
 * Generate a semantic search query based on component context
 * @param {string} componentType - Type of component (e.g., 'HeroSection', 'ProductCard')
 * @param {string} alt - Alt text or description
 * @param {object} screenContext - Screen metadata (name, category, etc.)
 * @returns {string} - Optimized search query
 */
export function generatePexelsQuery(componentType, alt, screenContext = {}) {
    // Priority 1: Use alt text if meaningful
    if (alt && alt.length > 3 && !['image', 'photo', 'picture'].includes(alt.toLowerCase())) {
        return alt;
    }

    // Priority 2: Use screen context
    const screenName = screenContext.name || '';
    const screenCategory = screenContext.category || '';

    if (screenCategory) {
        return screenCategory;
    }

    if (screenName && screenName.length > 3) {
        // Extract meaningful keywords from screen name
        const cleanName = screenName
            .replace(/screen|page|view/gi, '')
            .trim();

        if (cleanName.length > 2) {
            return cleanName;
        }
    }

    // Priority 3: Component-type based defaults
    const componentDefaults = {
        'HeroSection': 'modern abstract gradient',
        'ProductCard': 'product photography',
        'Image': 'minimal clean',
        'IllustrationHeader': 'illustration design',
        'Avatar': 'person portrait',
    };

    return componentDefaults[componentType] || 'abstract modern';
}
