# backend/prompt_refiner.py - API 0: Prompt Enhancement Layer
import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Import the unified LLM client (will use dedicated API key for refiner)
from llm_client import send_chat

###############################################################################
# 🎯 PROMPT REFINEMENT SYSTEM PROMPT
###############################################################################

PROMPT_REFINER_SYSTEM = """You are an expert UI/UX requirements analyst and prompt engineer.

YOUR TASK: Transform user's raw prompt into a detailed, structured prompt optimized for mobile UI generation.

TRANSFORMATION RULES:
1. **Expand Vague Terms**: "login" → "modern login screen with email/password, social auth (Google, Apple), forgot password"
2. **Add Context**: Always specify device type (mobile), design style (modern/minimal), color preferences
3. **Identify Missing Details**: If user says "app", ask yourself: What screens? What features? What flow?
4. **Normalize Language**: Map casual terms to specific components:
   - "buttons" → GradientButton, SocialButton
   - "list" → CardList, ProductCard, ListItem
   - "form" → IconInput, TextInput, PasswordInput
   - "profile" → Avatar, StatCard, HeroSection

5. **Screen Specification**: If multiple screens implied, list them explicitly
6. **Design Assumptions**: Add reasonable defaults based on industry standards:
   - Auth screens → social login, modern card design
   - Ecommerce → search, grid layout, floating cart button
   - Social → feed, posts, avatars, like/comment actions
   - Dashboard → stats cards, progress bars, charts

OUTPUT FORMAT (3-4 lines, structured):
Line 1: Core intent and screen types
Line 2: Key features and components
Line 3: Design style and interactions
Line 4 (optional): Additional context or constraints

EXAMPLES:

INPUT: "login screen"
OUTPUT: Create a modern mobile authentication screen with email/password login fields using IconInput components. Include social authentication buttons for Google and Apple, a forgot password link, and sign-up navigation. Use a clean card-based layout with gradient buttons in teal theme and IllustrationHeader at the top for welcoming users.

INPUT: "shopping app"
OUTPUT: Build a complete e-commerce mobile application with three main screens: product listing, cart, and checkout. Product listing should feature a SearchInput at top, Grid layout with ProductCard components showing images, titles, prices, and ratings. Include a FloatingActionButton for cart access. Cart screen should display CartItem components with QuantityControl and PriceBreakdown. Use orange gradient theme for commerce feel.

INPUT: "social feed"
OUTPUT: Create a social media feed screen with CardList of posts, each showing Avatar, user name, post content, images, and interaction buttons (like, comment, share). Include AppBar with search and notifications, and TabBar at bottom for navigation. Add a FloatingActionButton for creating new posts. Use modern card design with avatars and StatCards for profile metrics. Apply vibrant color theme suitable for social engagement.

INPUT: "dashboard"
OUTPUT: Design an analytics dashboard screen with Grid layout of StatCards displaying key metrics (revenue, users, growth, conversion). Include ProgressBar components for goal tracking with labels showing current vs target values. Use Card containers to group related statistics. Add AppBar with date range subtitle and filter actions. Apply professional blue/green color theme suitable for business analytics.

INPUT: "settings page"
OUTPUT: Create a settings screen with FormSection groups organizing preferences. Use List with ListItem components featuring icons, titles, and trailing elements (Switch for toggles, chevron-right for navigation). Include sections for Account (Edit Profile, Privacy), Preferences (Notifications, Dark Mode), and Support (Help, Terms). Add Avatar at top for profile picture with edit option. Use clean, organized layout with proper spacing.

CRITICAL RULES:
- Output ONLY the refined prompt (3-4 lines)
- NO JSON, NO markdown, NO explanations
- Be specific about component types (IconInput, GradientButton, ProductCard, etc.)
- Include design style hints (modern, clean, card-based, gradient)
- Mention color themes when relevant (teal for tech, orange for commerce, blue for business)
- Always specify if multiple screens are needed

Now refine this user prompt:"""

###############################################################################
# 🚀 CORE REFINER FUNCTION
###############################################################################

async def refine_prompt(raw_prompt: str, timeout: int = 15) -> Dict[str, Any]:
    """
    API 0: Transform raw user prompt into structured, detailed prompt.
    
    Args:
        raw_prompt: User's original input (can be vague, short, casual)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing:
        - original_prompt: User's raw input
        - refined_prompt: Enhanced 3-4 line structured prompt
        - refinement_applied: Boolean indicating if refinement was successful
        - metadata: Additional info (word count, detected keywords, etc.)
    """
    
    # Fallback in case of API failure
    fallback_result = {
        "original_prompt": raw_prompt,
        "refined_prompt": raw_prompt,  # Pass through unchanged
        "refinement_applied": False,
        "metadata": {
            "reason": "API call failed or skipped",
            "original_word_count": len(raw_prompt.split()),
            "refined_word_count": len(raw_prompt.split())
        }
    }
    
    # Skip refinement for empty prompts
    if not raw_prompt or not raw_prompt.strip():
        fallback_result["metadata"]["reason"] = "Empty prompt"
        return fallback_result
    
    # Skip refinement if prompt is already detailed (>50 words)
    word_count = len(raw_prompt.split())
    if word_count > 50:
        print(f"ℹ️  [REFINER] Prompt already detailed ({word_count} words), skipping refinement")
        fallback_result["refinement_applied"] = False
        fallback_result["metadata"]["reason"] = "Already detailed"
        return fallback_result
    
    try:
        print(f"🔄 [API 0 - REFINER] Refining prompt: '{raw_prompt[:100]}...'")
        
        # Build the full prompt for the LLM
        full_prompt = f"{PROMPT_REFINER_SYSTEM}\n\nUSER PROMPT: {raw_prompt}\n\nREFINED PROMPT:"
        
        # Call LLM using dedicated "refiner" route
        refined_text = await asyncio.wait_for(
            send_chat(full_prompt, route="refiner", timeout=timeout),
            timeout=timeout + 5
        )
        
        # Clean up the response
        refined_text = refined_text.strip()
        
        # Remove common artifacts
        refined_text = refined_text.replace("REFINED PROMPT:", "").strip()
        refined_text = refined_text.replace("OUTPUT:", "").strip()
        
        # Validate refinement quality
        refined_word_count = len(refined_text.split())
        
        # If refined prompt is too short or too similar to original, use fallback
        if refined_word_count < word_count + 5:
            print(f"⚠️  [REFINER] Refinement too short, using original")
            return fallback_result
        
        print(f"✅ [API 0 - REFINER] Successfully refined prompt")
        print(f"   Original: {word_count} words → Refined: {refined_word_count} words")
        
        # Detect keywords for metadata
        detected_keywords = _detect_keywords(refined_text)
        
        return {
            "original_prompt": raw_prompt,
            "refined_prompt": refined_text,
            "refinement_applied": True,
            "metadata": {
                "original_word_count": word_count,
                "refined_word_count": refined_word_count,
                "expansion_ratio": round(refined_word_count / word_count, 2),
                "detected_keywords": detected_keywords,
                "reason": "Successfully refined"
            }
        }
        
    except asyncio.TimeoutError:
        print(f"⚠️  [REFINER] Timeout - using original prompt")
        fallback_result["metadata"]["reason"] = "Timeout"
        return fallback_result
        
    except Exception as e:
        print(f"⚠️  [REFINER] Error: {e} - using original prompt")
        fallback_result["metadata"]["reason"] = f"Error: {str(e)[:50]}"
        return fallback_result


###############################################################################
# 🛠️ HELPER FUNCTIONS
###############################################################################

def _detect_keywords(text: str) -> list:
    """
    Detect UI-related keywords in the refined prompt for validation.
    """
    keywords = {
        "components": ["button", "input", "card", "grid", "avatar", "icon", "image", "header"],
        "screens": ["login", "signup", "cart", "checkout", "feed", "profile", "dashboard", "settings"],
        "design": ["modern", "clean", "gradient", "card-based", "minimal", "bold", "elegant"],
        "colors": ["teal", "blue", "purple", "green", "orange", "vibrant"]
    }
    
    text_lower = text.lower()
    detected = []
    
    for category, terms in keywords.items():
        for term in terms:
            if term in text_lower:
                detected.append(term)
    
    return list(set(detected))[:10]  # Return up to 10 unique keywords


def validate_refinement(original: str, refined: str) -> bool:
    """
    Validate that the refinement actually improved the prompt.
    
    Criteria:
    - Refined version is longer
    - Contains more specific UI terms
    - Has structural improvements
    """
    orig_words = len(original.split())
    refined_words = len(refined.split())
    
    # Must be at least 30% longer
    if refined_words < orig_words * 1.3:
        return False
    
    # Must contain UI-specific terms
    ui_terms = ["screen", "button", "input", "card", "component", "layout", "design"]
    has_ui_terms = any(term in refined.lower() for term in ui_terms)
    
    return has_ui_terms


###############################################################################
# 🧪 TESTING & DIAGNOSTICS
###############################################################################

async def test_refiner():
    """Test the prompt refiner with various inputs"""
    test_cases = [
        "login screen",
        "shopping app",
        "social feed",
        "dashboard with stats",
        "settings page",
        "ecommerce",
        "Modern login and signup screens with social auth and gradient buttons",  # Already detailed
        "",  # Empty
    ]
    
    print("\n" + "="*80)
    print("🧪 TESTING PROMPT REFINER (API 0)")
    print("="*80)
    
    for i, test_prompt in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: '{test_prompt}'")
        
        result = await refine_prompt(test_prompt)
        
        print(f"Refined: {result['refinement_applied']}")
        if result['refinement_applied']:
            print(f"Output ({result['metadata']['refined_word_count']} words):")
            print(f"  {result['refined_prompt'][:200]}...")
        else:
            print(f"Reason: {result['metadata']['reason']}")


###############################################################################
# 📊 STATISTICS & MONITORING
###############################################################################

class RefinerStats:
    """Track refinement statistics for monitoring"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_refinements = 0
        self.failed_refinements = 0
        self.skipped_refinements = 0
        self.avg_expansion_ratio = 0.0
        self.total_expansion_ratio = 0.0
    
    def record(self, result: Dict[str, Any]):
        """Record a refinement result"""
        self.total_requests += 1
        
        if result['refinement_applied']:
            self.successful_refinements += 1
            expansion = result['metadata'].get('expansion_ratio', 1.0)
            self.total_expansion_ratio += expansion
            self.avg_expansion_ratio = self.total_expansion_ratio / self.successful_refinements
        elif result['metadata']['reason'] == "Already detailed":
            self.skipped_refinements += 1
        else:
            self.failed_refinements += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        success_rate = (self.successful_refinements / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful": self.successful_refinements,
            "failed": self.failed_refinements,
            "skipped": self.skipped_refinements,
            "success_rate": round(success_rate, 2),
            "avg_expansion_ratio": round(self.avg_expansion_ratio, 2)
        }
    
    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()
        print("\n📊 REFINER STATISTICS")
        print("="*50)
        print(f"Total Requests:      {stats['total_requests']}")
        print(f"Successful:          {stats['successful']} ({stats['success_rate']}%)")
        print(f"Failed:              {stats['failed']}")
        print(f"Skipped:             {stats['skipped']}")
        print(f"Avg Expansion Ratio: {stats['avg_expansion_ratio']}x")


# Global stats instance
refiner_stats = RefinerStats()


###############################################################################
# 🚀 EXPORT PUBLIC API
###############################################################################

__all__ = [
    "refine_prompt",
    "validate_refinement",
    "test_refiner",
    "refiner_stats",
    "RefinerStats"
]


###############################################################################
# 🎮 CLI TESTING INTERFACE
###############################################################################

if __name__ == "__main__":
    import sys
    
    async def main():
        print("\n" + "="*80)
        print("🎯 PROMPT REFINER (API 0) - CLI Testing")
        print("="*80)
        
        if len(sys.argv) > 1:
            if sys.argv[1] == "--test":
                await test_refiner()
            
            elif sys.argv[1] == "--demo":
                print("\n🎮 INTERACTIVE DEMO")
                print("="*80)
                
                while True:
                    prompt = input("\nEnter prompt to refine (or 'quit'): ").strip()
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if prompt:
                        result = await refine_prompt(prompt)
                        refiner_stats.record(result)
                        
                        print(f"\n✅ RESULT:")
                        print(f"Applied: {result['refinement_applied']}")
                        print(f"Refined Prompt:\n{result['refined_prompt']}\n")
                        print(f"Metadata: {result['metadata']}")
                
                refiner_stats.print_stats()
            
            else:
                # Refine a single prompt from command line
                prompt = " ".join(sys.argv[1:])
                result = await refine_prompt(prompt)
                print(f"\nOriginal: {result['original_prompt']}")
                print(f"\nRefined:\n{result['refined_prompt']}")
                print(f"\nMetadata: {result['metadata']}")
        
        else:
            print("\n💡 USAGE:")
            print("  python prompt_refiner.py --test              # Run test suite")
            print("  python prompt_refiner.py --demo              # Interactive demo")
            print("  python prompt_refiner.py 'your prompt here'  # Refine single prompt")
            print("\n📚 IMPORT IN YOUR CODE:")
            print("  from prompt_refiner import refine_prompt")
            print("  result = await refine_prompt('login screen')")
    
    asyncio.run(main())