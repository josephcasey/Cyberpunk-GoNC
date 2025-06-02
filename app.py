import streamlit as st
from PIL import Image, ImageDraw
import os
import json
from matplotlib.path import Path
import numpy as np
import random
import math

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

# Load game data
@st.cache_data
def load_game_data():
    """Load game state and gang data"""
    try:
        # Load game state
        with open('game_state.json', 'r') as f:
            game_state = json.load(f)
        
        # Load gang data
        with open('gangs.json', 'r') as f:
            gangs = json.load(f)
        
        return game_state, gangs
    except Exception as e:
        st.error(f"Error loading game data: {e}")
        return None, None

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

def get_district_center(district_name, boundaries):
    """Calculate the center point of a district for unit placement"""
    if not boundaries:
        return None
    
    # Calculate centroid of the polygon
    x_coords = [point[0] for point in boundaries]
    y_coords = [point[1] for point in boundaries]
    
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    
    return (int(center_x), int(center_y))

def create_unit_positions(center, unit_count, spread=30):
    """Create positions for units around the district center"""
    if not center or unit_count == 0:
        return []
    
    positions = []
    center_x, center_y = center
    
    if unit_count == 1:
        positions.append((center_x, center_y))
    else:
        # Arrange units in a circle around the center
        for i in range(unit_count):
            angle = (2 * math.pi * i) / unit_count
            offset_x = int(spread * math.cos(angle))
            offset_y = int(spread * math.sin(angle))
            
            pos_x = center_x + offset_x
            pos_y = center_y + offset_y
            positions.append((pos_x, pos_y))
    
    return positions

def draw_units_on_image(image, game_state, gangs, scale_factor):
    """Draw gang units as colored dots on the image"""
    # Create a copy of the image to draw on
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    print(f"\n🎨 DEBUG: draw_units_on_image called with scale_factor={scale_factor}")
    
    # Process each district
    units_drawn = 0
    for district_name, district_data in game_state['districts'].items():
        print(f"  📍 Processing district: {district_name}")
        
        if 'units' not in district_data or not district_data['units']:
            print(f"    ❌ No units in {district_name}")
            continue
            
        print(f"    ✅ Units found in {district_name}: {district_data['units']}")
        
        # Map district names (handle case differences)
        boundary_key = district_name
        if boundary_key not in DISTRICT_BOUNDARIES:
            # Try title case
            boundary_key = district_name.title()
            if boundary_key not in DISTRICT_BOUNDARIES:
                # Try with space handling
                boundary_key = district_name.replace('_', ' ').title()
                if boundary_key not in DISTRICT_BOUNDARIES:
                    print(f"    ❌ No boundary found for {district_name}")
                    continue
        
        print(f"    🗺️ Using boundary key: {boundary_key}")
        
        # Get district center
        boundaries = DISTRICT_BOUNDARIES[boundary_key]
        center = get_district_center(district_name, boundaries)
        
        if not center:
            print(f"    ❌ Could not calculate center for {district_name}")
            continue
        
        print(f"    📍 District center: {center}")
        
        # Scale center to display coordinates
        display_center = (int(center[0] * scale_factor), int(center[1] * scale_factor))
        print(f"    📍 Display center: {display_center}")
        
        # Process units for each gang in this district
        gang_offset = 0
        for gang_id, units in district_data['units'].items():
            if not units:
                continue
                
            print(f"      🎭 Processing gang {gang_id} with {len(units)} units")
                
            # Get gang color
            gang_name = None
            gang_color = "gray"  # Default color
            
            # Find gang name and color
            for name, data in gangs.items():
                if data.get('id') == gang_id:
                    gang_name = name
                    gang_color = data.get('color', 'gray')
                    break
            
            # Convert color names to RGB-like values for PIL
            color_map = {
                'red': '#FF0000',
                'lime': '#00FF00', 
                'blue': '#0000FF',
                'pink': '#FF69B4',
                'purple': '#800080',
                'cyan': '#00FFFF',
                'yellow': '#FFFF00',
                'gray': '#808080'
            }
            
            if gang_color in color_map:
                gang_color = color_map[gang_color]
            elif not gang_color.startswith('#'):
                gang_color = '#808080'  # Default gray
            
            # Create unit positions
            unit_count = len(units)
            
            # Offset each gang's units to avoid overlap
            offset_center = (display_center[0] + gang_offset, display_center[1])
            positions = create_unit_positions(offset_center, unit_count, spread=int(20 * scale_factor))
            
            print(f"      🎨 Drawing {len(positions)} units at positions: {positions}")
            
            # Draw units
            for i, pos in enumerate(positions):
                x, y = pos
                radius = int(5 * scale_factor)  # Scale radius
                
                print(f"        🔵 Drawing unit {i+1} at ({x}, {y}) with radius {radius}")
                
                # Draw unit dot
                draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                           fill=gang_color, outline='black', width=1)
                
                units_drawn += 1
                
                # Optional: Add unit type indicator (different sizes/shapes)
                if i < len(units):
                    unit_type = units[i]
                    if "drone" in unit_type:
                        # Draw smaller white dot for drones
                        small_radius = int(2 * scale_factor)
                        draw.ellipse([x-small_radius, y-small_radius, x+small_radius, y+small_radius], 
                                   fill='white', outline=gang_color, width=1)
                        print(f"        ⚪ Added drone indicator")
            
            gang_offset += int(50 * scale_factor)  # Move next gang's units
    
    print(f"🎨 DEBUG: Total units drawn: {units_drawn}")
    return img_copy

# Initialize session state
if 'click_history' not in st.session_state:
    st.session_state.click_history = []

# UI
st.title("🗺️ Night City: Interactive Gang Territory Map")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive District Map")
    
    # Load image and game data
    display_img, original_size, scale_factor = load_image()
    game_state, gangs = load_game_data()
    
    # Unit visualization toggle
    show_units = st.checkbox("🎯 Show Gang Units", value=True, help="Display gang units as colored dots on the map")
    
    if display_img and HAS_IMAGE_COORDS:
        # Apply unit visualization if enabled
        final_img = display_img
        if show_units and game_state and gangs:
            final_img = draw_units_on_image(display_img, game_state, gangs, scale_factor)
            st.info("👆 Click anywhere on the map to detect districts! Colored dots show gang units.")
        else:
            st.info("👆 Click anywhere on the map to detect which district you clicked!")
        
        # Get click coordinates
        clicked_coords = streamlit_image_coordinates(
            final_img, 
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
                
                # Show gang information for this district
                if game_state and gangs and detected_district in game_state['districts']:
                    district_data = game_state['districts'][detected_district]
                    if 'units' in district_data and district_data['units']:
                        st.write("**Active Gangs in this District:**")
                        for gang_id, units in district_data['units'].items():
                            if units:
                                # Find gang info
                                gang_name = None
                                for name, data in gangs.items():
                                    if data.get('id') == gang_id:
                                        gang_name = name
                                        break
                                if gang_name:
                                    st.write(f"• {gang_name}: {len(units)} units")
                    
                    # Show district status
                    if 'dominant' in district_data and district_data['dominant']:
                        dom_gang = None
                        for name, data in gangs.items():
                            if data.get('id') == district_data['dominant']:
                                dom_gang = name
                                break
                        if dom_gang:
                            st.write(f"🏴 **Dominant Gang:** {dom_gang}")
                
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

    # Separate unit visualization area for debugging
    if show_units and game_state and gangs:
        st.subheader("🔍 Gang Unit Debug Visualization")
        st.write("This area shows if gang units are being generated correctly:")
        
        # Create a simple visualization canvas
        debug_canvas = Image.new('RGB', (400, 300), 'white')
        debug_draw = ImageDraw.Draw(debug_canvas)
        
        # Add grid
        for i in range(0, 400, 50):
            debug_draw.line([(i, 0), (i, 300)], fill='lightgray', width=1)
        for i in range(0, 300, 50):
            debug_draw.line([(0, i), (400, i)], fill='lightgray', width=1)
        
        y_offset = 50
        unit_count = 0
        
        for district_name, district_data in game_state['districts'].items():
            if 'units' not in district_data or not district_data['units']:
                continue
                
            st.write(f"**{district_name}:**")
            
            x_offset = 50
            for gang_id, units in district_data['units'].items():
                if not units:
                    continue
                    
                # Get gang info
                gang_name = None
                gang_color = "gray"
                for name, data in gangs.items():
                    if data.get('id') == gang_id:
                        gang_name = name
                        gang_color = data.get('color', 'gray')
                        break
                
                # Convert color
                color_map = {
                    'red': '#FF0000',
                    'lime': '#00FF00', 
                    'blue': '#0000FF',
                    'pink': '#FF69B4',
                    'purple': '#800080',
                    'cyan': '#00FFFF',
                    'yellow': '#FFFF00',
                    'gray': '#808080'
                }
                
                if gang_color in color_map:
                    gang_color = color_map[gang_color]
                elif not gang_color.startswith('#'):
                    gang_color = '#808080'
                
                # Draw units in debug area
                for i, unit_type in enumerate(units):
                    x = x_offset + (i * 25)
                    y = y_offset
                    
                    if x < 380:  # Stay within bounds
                        # Draw unit dot
                        debug_draw.ellipse([x-8, y-8, x+8, y+8], fill=gang_color, outline='black', width=2)
                        
                        # Mark drones differently
                        if "drone" in unit_type:
                            debug_draw.ellipse([x-4, y-4, x+4, y+4], fill='white', outline='black', width=1)
                        
                        unit_count += 1
                
                st.write(f"  • {gang_name}: {len(units)} units ({gang_color})")
                x_offset += len(units) * 25 + 20
            
            y_offset += 50
        
        st.image(debug_canvas, caption=f"Debug: Generated {unit_count} unit dots")
        
        if unit_count == 0:
            st.warning("⚠️ No units found in game state!")
        else:
            st.success(f"✅ Successfully generated {unit_count} unit visualizations")

with col2:
    st.subheader("Detection Results")
    
    # Show unit information if available
    game_state, gangs = load_game_data()
    if game_state and gangs:
        st.subheader("🎯 Gang Units Overview")
        
        # Gang legend
        st.write("**Gang Colors:**")
        active_gangs = set()
        for district_data in game_state['districts'].values():
            if 'units' in district_data:
                active_gangs.update(district_data['units'].keys())
        
        for gang_id in active_gangs:
            for name, data in gangs.items():
                if data.get('id') == gang_id:
                    color = data.get('color', 'gray')
                    # Create a simple color indicator
                    color_emoji = {
                        'red': '🔴',
                        'lime': '🟢', 
                        'blue': '🔵',
                        'pink': '🩷',
                        'purple': '🟣',
                        'cyan': '🔵',
                        'yellow': '🟡',
                        'gray': '⚫'
                    }
                    emoji = color_emoji.get(color, '⚫')
                    st.write(f"  {emoji} **{name}**")
                    break
        
        st.write("**District Units:**")
        for district_name, district_data in game_state['districts'].items():
            if 'units' in district_data and district_data['units']:
                st.write(f"**{district_name}:**")
                for gang_id, units in district_data['units'].items():
                    if units:
                        # Find gang info
                        gang_name = None
                        gang_color = "gray"
                        for name, data in gangs.items():
                            if data.get('id') == gang_id:
                                gang_name = name
                                gang_color = data.get('color', 'gray')
                                break
                        
                        if gang_name:
                            st.write(f"  • {gang_name} ({len(units)} units)")
                            # Show unit types
                            unit_types = {}
                            for unit in units:
                                unit_types[unit] = unit_types.get(unit, 0) + 1
                            for unit_type, count in unit_types.items():
                                st.write(f"    - {unit_type}: {count}")
                        else:
                            st.write(f"  • {gang_id} ({len(units)} units)")
        st.divider()
    
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
st.subheader("📊 Game Statistics")

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
        
        most_clicked = max(district_clicks.keys(), key=lambda k: district_clicks[k]) if district_clicks else "None"
        st.metric("Most Clicked District", most_clicked)
        st.metric("Total Clicks", len(st.session_state.click_history))
    else:
        st.metric("Most Clicked District", "None")
        st.metric("Total Clicks", 0)

with col3:
    # Show game round and phase info
    if game_state:
        st.metric("Game Round", game_state.get('round', 'Unknown'))
        st.metric("Current Phase", game_state.get('phase', 'Unknown').title())
    else:
        st.metric("Game Round", "N/A")
        st.metric("Current Phase", "N/A")

# Gang territory summary
if game_state and gangs:
    st.subheader("🏴 Territory Control")
    
    gang_territories = {}
    total_units = 0
    
    for district_name, district_data in game_state['districts'].items():
        if 'units' in district_data:
            for gang_id, units in district_data['units'].items():
                if units:
                    gang_name = None
                    for name, data in gangs.items():
                        if data.get('id') == gang_id:
                            gang_name = name
                            break
                    
                    if gang_name:
                        if gang_name not in gang_territories:
                            gang_territories[gang_name] = []
                        gang_territories[gang_name].append(f"{district_name} ({len(units)} units)")
                        total_units += len(units)
    
    if gang_territories:
        for gang_name, territories in gang_territories.items():
            st.write(f"**{gang_name}:** {', '.join(territories)}")
        
        st.write(f"**Total Units on Board:** {total_units}")

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
with st.expander("ℹ️ How to Use This Interface"):
    st.write("""
    **Gang Unit Visualization:**
    - Colored dots represent gang units positioned in each district
    - Each gang has a unique color (see legend in the sidebar)
    - Units are clustered around district centers
    - Drones appear as smaller white dots inside the gang color
    - Toggle "Show Gang Units" to hide/show unit visualization
    
    **District Detection:**
    - Click anywhere on the map to detect which district you clicked
    - Uses point-in-polygon algorithm for accurate detection
    - Shows active gangs and dominant faction for clicked districts
    - All detection uses original image coordinates for precision
    
    **Game Information:**
    - Current game state shows round and phase information
    - Territory control summary shows which gangs control which districts
    - Unit counts and types are displayed for each active gang
    
    **Technical Details:**
    - District boundaries defined by collected coordinate polygons
    - Automatic coordinate scaling from display to original image size
    - Uses matplotlib's Path.contains_point() for polygon detection
    - Real-time click history tracking with duplicate prevention
    """)
    
    st.write("**Unit Type Legend:**")
    st.write("• **Large colored dots:** Basic gang units (solo, techie, netrunner)")
    st.write("• **Small white dots:** Drone units")
    st.write("• **Gang colors:** As shown in the sidebar legend")
