import streamlit as st
from PIL import Image
import os
import json

# Import streamlit-image-coordinates
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAS_IMAGE_COORDS = True
except ImportError:
    HAS_IMAGE_COORDS = False

# Configuration
st.set_page_config(page_title="Night City Coordinate Collector", layout="wide")

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

# Initialize session state
def init_session_state():
    if 'districts' not in st.session_state:
        st.session_state.districts = {
            "Watson": [(116,39), (887,36), (893,211), (866,254), (721,307), (629,313), (571,473), (516,506), (245,500), (98,353), (98,64), (119,43)],  # Pre-collected
            "Westbrook": [(629,309), (983,312), (985,819), (944,816), (655,645), (634,573), (519,501), (568,473), (632,309), (983,312)],  # Pre-collected
            "City Center": [(58,501), (517,501), (629,573), (655,642), (517,814), (483,826), (445,837), (412,837), (378,821), (350,791), (337,742), (69,755), (25,698), (23,540), (56,499)],  # Pre-collected
            "Heywood": [[23,698],[66,760],[332,744],[358,801],[396,826],[442,844],[486,832],[532,808],[657,642],[762,714],[460,1088],[176,1090],[56,960],[20,993],[20,698]],
            "Pacifica": [[20,995],[51,962],[176,1090],[463,1090],[463,1118],[691,1331],[547,1523],[20,1520],[23,993]],
            "Santo Domingo": [[765,714],[942,819],[988,819],[1018,816],[1018,1525],[565,1523],[706,1323],[478,1116],[478,1090],[770,727],[768,711]]
        }
    if 'last_click' not in st.session_state:
        st.session_state.last_click = None

init_session_state()

# UI
st.title("🗺️ Night City: Clean Coordinate Collector")

col1, col2 = st.columns([2, 1])

with col1:
    # District selection
    current_district = st.selectbox(
        "Select district to map:", 
        ["Watson", "Westbrook", "City Center", "Heywood", "Pacifica", "Santo Domingo"],
        index=3  # Start with Heywood (next district)
    )
    
    # Show current progress
    current_count = len(st.session_state.districts[current_district])
    st.write(f"**{current_district}**: {current_count} points collected")
    
    # Load image
    display_img, original_size, scale_factor = load_image()
    
    if display_img and HAS_IMAGE_COORDS:
        st.write("👆 Click on the map to add boundary points")
        
        # Create unique key for each district to avoid conflicts
        image_key = f"map_clicks_{current_district.lower().replace(' ', '_')}"
        
        # Get click coordinates
        clicked_coords = streamlit_image_coordinates(
            display_img, 
            key=image_key
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
            
            # Check if this is a new click (avoid duplicates)
            new_point = (orig_x, orig_y)
            if st.session_state.last_click != new_point:
                st.session_state.last_click = new_point
                st.session_state.districts[current_district].append(new_point)
                
                # Visual feedback
                st.success(f"✅ Added point ({orig_x}, {orig_y}) to {current_district}")
                
                # Terminal output
                print(f"\n[{current_district}] New point: ({orig_x}, {orig_y})")
                print(f"JSON format: [{orig_x}, {orig_y}],")
                print(f"Total points for {current_district}: {len(st.session_state.districts[current_district])}")
                
                # Refresh the page to show updated count
                st.rerun()
    
    elif not HAS_IMAGE_COORDS:
        st.error("Please install: pip install streamlit-image-coordinates")
    else:
        st.error("Could not load image")

with col2:
    # Manual entry backup
    st.subheader("Manual Entry")
    manual_x = st.number_input("X:", value=0, step=1)
    manual_y = st.number_input("Y:", value=0, step=1)
    
    if st.button("Add Manual Point"):
        new_point = (manual_x, manual_y)
        st.session_state.districts[current_district].append(new_point)
        st.success(f"Added ({manual_x}, {manual_y})")
        print(f"\n[{current_district}] Manual: ({manual_x}, {manual_y})")
        st.rerun()
    
    # District management
    st.subheader("District Management")
    
    if st.button("Remove Last Point"):
        if st.session_state.districts[current_district]:
            removed = st.session_state.districts[current_district].pop()
            st.success(f"Removed {removed}")
            st.rerun()
        else:
            st.warning("No points to remove")
    
    if st.button("Clear District"):
        st.session_state.districts[current_district] = []
        st.success(f"Cleared {current_district}")
        st.rerun()
    
    if st.button("Reset All"):
        for district in st.session_state.districts:
            if district != "Watson":  # Keep Watson
                st.session_state.districts[district] = []
        st.success("Reset all except Watson")
        st.rerun()

# Display all collected coordinates
st.subheader("📋 Collected Coordinates")

for district, coords in st.session_state.districts.items():
    if coords:  # Only show districts with coordinates
        with st.expander(f"{district} ({len(coords)} points)", expanded=(district == current_district)):
            # Human readable
            coord_text = ", ".join([f"({x},{y})" for x, y in coords])
            st.text_area("Human readable:", coord_text, height=60, key=f"human_{district}")
            
            # JSON format
            json_text = json.dumps(coords, separators=(',', ':'))
            st.text_area("JSON format:", json_text, height=60, key=f"json_{district}")
            
            # Terminal output button
            if st.button(f"Print {district} to Terminal", key=f"print_{district}"):
                print(f"\n=== {district.upper()} COORDINATES ===")
                print(f"Human: {coord_text}")
                print(f"JSON: {json_text}")
                print(f"Points: {len(coords)}")
                st.success(f"Printed {district} coordinates to terminal")

# Export all data
if st.button("Export All to Terminal"):
    print("\n" + "="*50)
    print("NIGHT CITY DISTRICT COORDINATES - FULL EXPORT")
    print("="*50)
    
    for district, coords in st.session_state.districts.items():
        if coords:
            print(f"\n{district.upper()}:")
            print(f"  Points: {len(coords)}")
            print(f"  Human: {', '.join([f'({x},{y})' for x, y in coords])}")
            print(f"  JSON: {json.dumps(coords, separators=(',', ':'))}")
    
    print("\n" + "="*50)
    st.success("Full export printed to terminal!")
