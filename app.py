from streamlit_drawable_canvas import st_canvas
import streamlit as st
from PIL import Image
import os

# Use absolute path to ensure image loads correctly
image_path = os.path.join(os.path.dirname(__file__), "board_with_overlay.png")

try:
    board_img = Image.open(image_path)
    st.write(f"✅ Successfully loaded image: {image_path}")
except Exception as e:
    st.error(f"❌ Error loading image: {e}")
    # Fallback to the original image
    try:
        board_img = Image.open("districts_canvas_preview.jpg")
        st.write("✅ Using fallback image: districts_canvas_preview.jpg")
    except Exception as e2:
        st.error(f"❌ Error loading fallback image: {e2}")
        board_img = None

st.title("🗺️ Night City: Coordinate Collector")

st.write("**Instructions:**")
st.write("1. Select the district you're currently mapping")
st.write("2. Click around the district boundaries on the map")
st.write("3. Copy coordinates from the terminal output")
st.write("4. Use coordinates to build polygon boundaries offline")

if board_img is not None:
    canvas_result = st_canvas(
        background_image=board_img,
        update_streamlit=True,
        height=650,
        width=550,
        drawing_mode="point",   # point mode - single clicks create points
        point_display_radius=3,
        stroke_width=1,
        stroke_color="#FF0000",
        fill_color="#FF0000",
        key="district_canvas",
    )
else:
    st.error("Cannot create canvas - no background image available")
    canvas_result = None

# Display instructions
st.info("🎯 Click on the map to collect coordinates. Check the terminal for output!")

# Show current district selection for context
current_district = st.selectbox("Currently collecting points for:", 
                               ["Watson", "Westbrook", "City Center", "Heywood", "Pacifica", "Santo Domingo"],
                               help="This is just for reference - coordinates will be printed for any clicks")

# Debug: Show what we're getting from canvas
if canvas_result and canvas_result.json_data:
    st.write("**Debug - Canvas Data:**", canvas_result.json_data)

# When you click, Streamlit places a tiny "circle" object at the click point
if canvas_result and canvas_result.json_data and "objects" in canvas_result.json_data:
    st.write(f"**Debug - Found {len(canvas_result.json_data['objects'])} objects**")
    
    for obj in canvas_result.json_data["objects"]:
        st.write(f"**Debug - Object type:** {obj.get('type', 'unknown')}")
        
        # Handle different object types (circle, path, etc.)
        if obj["type"] in ["circle", "path", "line"]:
            # Get coordinates based on object type
            if obj["type"] == "circle":
                # For point mode, the circle represents the click point
                cx = int(obj["left"] + obj.get("radius", 0))
                cy = int(obj["top"] + obj.get("radius", 0))
            elif obj["type"] == "path":
                # For freedraw mode, get the starting point
                if "path" in obj:
                    # Parse SVG path to get coordinates
                    path_str = obj["path"]
                    if "M" in path_str:
                        try:
                            coords = path_str.split("M")[1].split("L")[0].strip().split()
                            if len(coords) >= 2:
                                cx = int(float(coords[0]))
                                cy = int(float(coords[1]))
                            else:
                                continue
                        except:
                            continue
                    else:
                        continue
                else:
                    continue
            elif obj["type"] == "line":
                # For line objects, get the starting point
                cx = int(obj.get("x1", obj.get("left", 0)))
                cy = int(obj.get("y1", obj.get("top", 0)))
            else:
                continue
            
            # Print coordinate in easy-to-copy format
            print(f"[{current_district}] Point: ({cx}, {cy})")
            print(f"JSON format: [{cx}, {cy}],")
            
            # Also show in the web interface
            st.success(f"📍 Clicked at ({cx}, {cy}) - Check terminal for copy-paste format!")
            
            # Optional: Show running list of recent clicks
            if 'recent_clicks' not in st.session_state:
                st.session_state.recent_clicks = []
            
            st.session_state.recent_clicks.append((cx, cy, current_district))
            if len(st.session_state.recent_clicks) > 10:  # Keep only last 10
                st.session_state.recent_clicks.pop(0)

# Show recent clicks in sidebar
with st.sidebar:
    st.subheader("📋 Recent Clicks")
    if 'recent_clicks' in st.session_state and st.session_state.recent_clicks:
        for i, (x, y, district) in enumerate(reversed(st.session_state.recent_clicks)):
            st.write(f"{i+1}. {district}: ({x}, {y})")
        
        if st.button("Clear Recent Clicks"):
            st.session_state.recent_clicks = []
            st.rerun()
    else:
        st.write("No clicks yet")
