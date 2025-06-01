import streamlit as st
from PIL import Image
import os

# Try to import streamlit-image-coordinates
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAS_IMAGE_COORDS = True
except ImportError:
    HAS_IMAGE_COORDS = False
    st.error("Please install streamlit-image-coordinates: pip install streamlit-image-coordinates")

# Load image
image_path = os.path.join(os.path.dirname(__file__), "board_with_overlay.png")

try:
    board_img = Image.open(image_path)
    # Resize for better display
    original_size = board_img.size
    max_width = 700
    max_height = 500
    
    scale_factor = min(max_width / original_size[0], max_height / original_size[1])
    new_width = int(original_size[0] * scale_factor)
    new_height = int(original_size[1] * scale_factor)
    
    display_img = board_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    st.write(f"✅ Image loaded: {original_size} → {(new_width, new_height)} (scale: {scale_factor:.2f})")
    
except Exception as e:
    st.error(f"❌ Error loading image: {e}")
    display_img = None
    scale_factor = 1.0

st.title("🗺️ Night City: District Coordinate Collector")

# Instructions
st.info("""
🎯 **Instructions:**
1. Select the district you're mapping from the dropdown
2. Click on the map to collect boundary points
3. Watch the terminal for coordinate output
4. Use manual entry as backup if clicks don't work
""")

# District selection
current_district = st.selectbox(
    "Currently collecting points for:", 
    ["Watson", "Westbrook", "City Center", "Heywood", "Pacifica", "Santo Domingo"],
    index=1,  # Default to Westbrook (next district)
    help="Select which district you're currently mapping"
)

# Clear session state button for fresh start
if st.button("🔄 Reset Session (Clear All Data)"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Session reset! Fresh start for coordinate collection.")
    st.rerun()

# Image click detection
if display_img is not None and HAS_IMAGE_COORDS:
    st.write(f"🖱️ **Click on the map to collect {current_district} boundary points**")
    
    # Unique key based on district to avoid conflicts
    map_key = f"map_{current_district.lower().replace(' ', '_')}"
    
    # Get click coordinates
    click_coords = streamlit_image_coordinates(display_img, key=map_key)
    
    if click_coords is not None:
        try:
            # Handle different coordinate formats
            if hasattr(click_coords, 'get'):
                # Dictionary format
                display_x = click_coords.get('x', click_coords.get(0, 0))
                display_y = click_coords.get('y', click_coords.get(1, 0))
            elif isinstance(click_coords, (list, tuple)) and len(click_coords) >= 2:
                # List/tuple format
                display_x, display_y = click_coords[0], click_coords[1]
            else:
                # Unknown format - show debug info
                st.error(f"Unknown coordinate format: {click_coords} (type: {type(click_coords)})")
                display_x, display_y = 0, 0
            
            # Convert to original image coordinates
            orig_x = int(display_x / scale_factor)
            orig_y = int(display_y / scale_factor)
            
            # Display success message
            st.success(f"📍 {current_district}: Display({display_x:.0f}, {display_y:.0f}) → Original({orig_x}, {orig_y})")
            
            # Print to terminal
            print(f"\n[{current_district}] Coordinate: ({orig_x}, {orig_y})")
            print(f"JSON: [{orig_x}, {orig_y}],")
            
            # Store in session state
            coord_key = f"coords_{current_district.lower().replace(' ', '_')}"
            if coord_key not in st.session_state:
                st.session_state[coord_key] = []
            
            # Add if not duplicate
            new_coord = (orig_x, orig_y)
            if new_coord not in st.session_state[coord_key]:
                st.session_state[coord_key].append(new_coord)
                st.balloons()
                
        except Exception as e:
            st.error(f"Error processing click: {e}")
            st.write(f"Raw click data: {click_coords}")

else:
    st.warning("⚠️ Image or click detection not available. Use manual entry below.")

# Display collected coordinates for current district
coord_key = f"coords_{current_district.lower().replace(' ', '_')}"
if coord_key in st.session_state and st.session_state[coord_key]:
    coords = st.session_state[coord_key]
    st.subheader(f"📋 {current_district} Coordinates ({len(coords)} points)")
    
    # Display coordinates
    coord_text = ", ".join([f"({x}, {y})" for x, y in coords])
    st.code(coord_text)
    
    # JSON format
    json_text = f'"{current_district}": {[list(coord) for coord in coords]}'
    st.code(json_text, language="json")
    
    # Remove last point button
    if st.button(f"❌ Remove Last {current_district} Point"):
        st.session_state[coord_key].pop()
        st.success("Removed last point")
        st.rerun()

# Show all collected districts
st.subheader("📊 All Districts Progress")
district_keys = [
    ("Watson", "coords_watson"),
    ("Westbrook", "coords_westbrook"), 
    ("City Center", "coords_city_center"),
    ("Heywood", "coords_heywood"),
    ("Pacifica", "coords_pacifica"),
    ("Santo Domingo", "coords_santo_domingo")
]

for district_name, key in district_keys:
    count = len(st.session_state.get(key, []))
    if count > 0:
        st.write(f"✅ **{district_name}**: {count} points")
    else:
        st.write(f"⬜ **{district_name}**: No points yet")

# Manual coordinate entry
st.subheader("✏️ Manual Entry (Backup Method)")
col1, col2 = st.columns(2)
with col1:
    manual_x = st.number_input("X coordinate", value=0, step=1, key="manual_x")
with col2:
    manual_y = st.number_input("Y coordinate", value=0, step=1, key="manual_y")

if st.button("➕ Add Manual Point"):
    coord_key = f"coords_{current_district.lower().replace(' ', '_')}"
    if coord_key not in st.session_state:
        st.session_state[coord_key] = []
    
    st.session_state[coord_key].append((manual_x, manual_y))
    st.success(f"Added manual point ({manual_x}, {manual_y}) to {current_district}")
    
    # Print to terminal
    print(f"\n[{current_district}] Manual Coordinate: ({manual_x}, {manual_y})")
    print(f"JSON: [{manual_x}, {manual_y}],")
    
    st.rerun()

# Quick actions
st.subheader("🛠️ Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Print All to Terminal"):
        print(f"\n=== ALL COLLECTED COORDINATES ===")
        for district_name, key in district_keys:
            coords = st.session_state.get(key, [])
            if coords:
                print(f"\n{district_name} ({len(coords)} points):")
                coord_list = [list(coord) for coord in coords]
                print(f'"{district_name}": {coord_list},')
        print(f"\n=== END COORDINATES ===")
        st.success("All coordinates printed to terminal")

with col2:
    if st.button(f"🗑️ Clear {current_district}"):
        coord_key = f"coords_{current_district.lower().replace(' ', '_')}"
        if coord_key in st.session_state:
            del st.session_state[coord_key]
        st.success(f"Cleared all {current_district} coordinates")
        st.rerun()

with col3:
    if st.button("💾 Export JSON"):
        all_coords = {}
        for district_name, key in district_keys:
            coords = st.session_state.get(key, [])
            if coords:
                all_coords[district_name] = [list(coord) for coord in coords]
        
        if all_coords:
            st.code(str(all_coords).replace("'", '"'), language="json")
        else:
            st.warning("No coordinates to export")

# Tips
with st.expander("💡 Tips for Better Coordinate Collection"):
    st.write("""
    - **Click slowly** - Give the app time to register each click
    - **Follow district outlines** - Use the colored borders on the map as guides
    - **8-12 points per district** - Enough for accurate boundary definition
    - **Work clockwise** - Consistent direction helps avoid crossing lines
    - **Check terminal output** - Coordinates appear immediately when registered
    - **Use manual entry** - If clicks aren't working, enter coordinates manually
    - **Reset session** - If the app becomes unresponsive, use the reset button
    """)
