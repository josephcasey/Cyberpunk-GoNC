import streamlit as st
from PIL import Image
import os
import json
from matplotlib.path import Path
import numpy as np

# Import streamlit-image-coordinates
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAS_IMAGE_COORDS = True
except ImportError:
    HAS_IMAGE_COORDS = False
    st.error("Please install: pip install streamlit-image-coordinates")

# Configuration
st.set_page_config(page_title="Night City: District Click Detection", layout="wide")

# District boundary coordinates (collected from your coordinate collector)
DISTRICT_BOUNDARIES = {
    "Watson": [(116,39), (887,36), (893,211), (866,254), (721,307), (629,313), (571,473), (516,506), (245,500), (98,353), (98,64), (119,43)],
    "Westbrook": [(629,309), (983,312), (985,819), (944,816), (655,645), (634,573), (519,501), (568,473), (632,309), (983,312)],
    "City Center": [(58,501), (517,501), (629,573), (655,642), (517,814), (483,826), (445,837), (412,837), (378,821), (350,791), (337,742), (69,755), (25,698), (23,540), (56,499)],
    "Heywood": [(23,698), (66,760), (332,744), (358,801), (396,826), (442,844), (486,832), (532,808), (657,642), (762,714), (460,1088), (176,1090), (56,960), (20,993), (20,698)],
    "Pacifica": [(20,995), (51,962), (176,1090), (463,1090), (463,1118), (691,1331), (547,1523), (20,1520), (23,993)],
    "Santo Domingo": [(765,714), (942,819), (988,819), (1018,816), (1018,1525), (565,1523), (706,1323), (478,1116), (478,1090), (770,727), (768,711)]
}

# Load and prepare image
@st.cache_data
def load_image():
    image_path = os.path.join(os.path.dirname(__file__), "board_with_overlay.png")
    try:
        board_img = Image.open(image_path)
        original_size = board_img.size
        
        # Resize for display
        max_width = 800
        max_height = 600
        scale_factor = min(max_width / original_size[0], max_height / original_size[1])
        new_width = int(original_size[0] * scale_factor)
        new_height = int(original_size[1] * scale_factor)
        
        display_img = board_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return display_img, original_size, scale_factor
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None, None, 1.0

def point_in_polygon(point, polygon):
    """Check if a point is inside a polygon using matplotlib's Path.contains_point"""
    try:
        path = Path(polygon)
        return path.contains_point(point)
    except Exception as e:
        st.error(f"Error in polygon detection: {e}")
        return False

def detect_district(x, y):
    """Detect which district a point belongs to"""
    point = (x, y)
    
    # Check each district
    for district_name, boundaries in DISTRICT_BOUNDARIES.items():
        if point_in_polygon(point, boundaries):
            return district_name
    
    return None  # No district found

# Initialize session state
if 'click_history' not in st.session_state:
    st.session_state.click_history = []

# UI
st.title("🗺️ Night City: District Click Detection Test")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive District Map")
    
    # Load image
    display_img, original_size, scale_factor = load_image()
    
    if display_img and HAS_IMAGE_COORDS:
        st.info("👆 Click anywhere on the map to detect which district you clicked!")
        
        # Get click coordinates
        clicked_coords = streamlit_image_coordinates(
            display_img, 
            key="district_detection"
        )
        
        # Process clicks
        if clicked_coords is not None:
            # Convert to original coordinates
            if isinstance(clicked_coords, dict):
                display_x = clicked_coords.get('x', 0)
                display_y = clicked_coords.get('y', 0)
            else:
                display_x, display_y = clicked_coords[0], clicked_coords[1]
            
            # Scale to original image size
            orig_x = int(display_x / scale_factor)
            orig_y = int(display_y / scale_factor)
            
            # Detect district
            detected_district = detect_district(orig_x, orig_y)
            
            if detected_district:
                st.success(f"🎯 **{detected_district}** detected!")
                st.write(f"📍 Click coordinates: ({orig_x}, {orig_y})")
                
                # Add to history
                click_record = {
                    "coordinates": (orig_x, orig_y),
                    "district": detected_district,
                    "display_coords": (int(display_x), int(display_y))
                }
                
                # Avoid duplicates
                if not st.session_state.click_history or st.session_state.click_history[-1]["coordinates"] != (orig_x, orig_y):
                    st.session_state.click_history.append(click_record)
                
                # Terminal output
                print(f"\n🎯 DISTRICT DETECTED: {detected_district}")
                print(f"   Coordinates: ({orig_x}, {orig_y})")
                print(f"   Display: ({int(display_x)}, {int(display_y)})")
                
            else:
                st.warning(f"❓ No district detected at ({orig_x}, {orig_y})")
                st.write("This might be outside all district boundaries or in a gap between districts.")
                
                # Terminal output
                print(f"\n❓ NO DISTRICT: ({orig_x}, {orig_y})")
    
    elif not HAS_IMAGE_COORDS:
        st.error("Please install: pip install streamlit-image-coordinates")
    else:
        st.error("Could not load image")

with col2:
    st.subheader("Detection Results")
    
    # Show district information
    st.write("**Available Districts:**")
    for district, coords in DISTRICT_BOUNDARIES.items():
        st.write(f"• **{district}**: {len(coords)} boundary points")
    
    # Manual coordinate test
    st.subheader("Manual Coordinate Test")
    test_x = st.number_input("Test X coordinate:", value=500, step=1)
    test_y = st.number_input("Test Y coordinate:", value=400, step=1)
    
    if st.button("Test Coordinate"):
        test_district = detect_district(test_x, test_y)
        if test_district:
            st.success(f"Coordinate ({test_x}, {test_y}) is in **{test_district}**")
        else:
            st.warning(f"Coordinate ({test_x}, {test_y}) is not in any district")
    
    # Click history
    if st.session_state.click_history:
        st.subheader("Click History")
        
        # Show recent clicks
        for i, click in enumerate(reversed(st.session_state.click_history[-5:])):  # Last 5 clicks
            coords = click["coordinates"]
            district = click["district"]
            st.write(f"{len(st.session_state.click_history) - i}. **{district}** at ({coords[0]}, {coords[1]})")
        
        # Clear history button
        if st.button("Clear History"):
            st.session_state.click_history = []
            st.rerun()

# District statistics
st.subheader("📊 District Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Districts", len(DISTRICT_BOUNDARIES))
    st.metric("Total Boundary Points", sum(len(coords) for coords in DISTRICT_BOUNDARIES.values()))

with col2:
    if st.session_state.click_history:
        # Count clicks per district
        district_clicks = {}
        for click in st.session_state.click_history:
            district = click["district"]
            district_clicks[district] = district_clicks.get(district, 0) + 1
        
        most_clicked = max(district_clicks, key=district_clicks.get) if district_clicks else "None"
        st.metric("Most Clicked District", most_clicked)
        st.metric("Total Clicks", len(st.session_state.click_history))
    else:
        st.metric("Most Clicked District", "None")
        st.metric("Total Clicks", 0)

with col3:
    # Show boundary info for largest/smallest districts
    largest_district = max(DISTRICT_BOUNDARIES, key=lambda d: len(DISTRICT_BOUNDARIES[d]))
    smallest_district = min(DISTRICT_BOUNDARIES, key=lambda d: len(DISTRICT_BOUNDARIES[d]))
    
    st.metric("Most Complex District", largest_district)
    st.metric("Simplest District", smallest_district)

# Export functionality
if st.button("Export All Data to Terminal"):
    print("\n" + "="*60)
    print("NIGHT CITY DISTRICT DETECTION - FULL DATA EXPORT")
    print("="*60)
    
    print("\nDISTRICT BOUNDARIES:")
    for district, coords in DISTRICT_BOUNDARIES.items():
        print(f"\n{district}:")
        print(f"  Boundary Points: {len(coords)}")
        print(f"  Coordinates: {coords}")
    
    if st.session_state.click_history:
        print(f"\nCLICK HISTORY ({len(st.session_state.click_history)} clicks):")
        for i, click in enumerate(st.session_state.click_history, 1):
            coords = click["coordinates"]
            district = click["district"]
            print(f"  {i}. {district} at ({coords[0]}, {coords[1]})")
    
    print("\n" + "="*60)
    st.success("Full data exported to terminal!")

# Instructions
with st.expander("ℹ️ How District Detection Works"):
    st.write("""
    **Point-in-Polygon Algorithm:**
    1. Each district is defined by a polygon made from boundary coordinates
    2. When you click, the algorithm checks if your click point is inside any district polygon
    3. Uses matplotlib's Path.contains_point() for accurate detection
    4. Returns the first matching district (districts shouldn't overlap)
    
    **Coordinate System:**
    - Uses original image coordinates (not display coordinates)
    - Automatically scales from display clicks to original image coordinates
    - All boundary coordinates are in original image space
    
    **Testing:**
    - Click anywhere on the map to test detection
    - Use manual coordinate entry to test specific points
    - Check click history to see detection accuracy
    """)
