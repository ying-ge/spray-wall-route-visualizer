import json
import cv2
import argparse
from pathlib import Path

# Global variable to store the last click coordinates
click_coords = None

def click_event(event, x, y, flags, params):
    global click_coords
    if event == cv2.EVENT_LBUTTONDOWN:
        click_coords = (x, y)
        print(f"Clicked at: ({x}, {y})")

def main(wall_dir):
    wall_path = Path(wall_dir)
    routes_path = wall_path / 'routes.json'
    holds_path = wall_path / 'output/data/holds.json'
    image_path = wall_path / 'image_base.png'

    if not all([routes_path.exists(), image_path.exists()]):
        print(f"Error: Ensure 'routes.json' and 'image_base.png' exist in '{wall_dir}'")
        return

    # Load existing holds data or initialize if not present
    holds_data = {}
    if holds_path.exists():
        with open(holds_path, 'r', encoding='utf-8') as f:
            holds_data = json.load(f)

    # Find all holds used in routes
    used_holds = set()
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_db = json.load(f)
        for route in routes_db.get('routes', []):
            for move in route.get('moves', []):
                used_holds.add(move['hold_id'])
            for foot_hold in route.get('holds', {}).get('foot', []):
                used_holds.add(foot_hold)

    # Determine missing holds
    missing_holds = sorted(list(used_holds - set(holds_data.keys())))

    if not missing_holds:
        print("✅ All holds used in routes are already defined. Nothing to do.")
        return

    print(f"Found {len(missing_holds)} missing holds: {', '.join(missing_holds)}")

    # Interactive session to add missing holds
    img = cv2.imread(str(image_path))
    window_name = "Interactive Hold Adder"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, click_event)
    
    global click_coords

    for hold_id in missing_holds:
        click_coords = None
        temp_img = img.copy()
        prompt = f"Please CLICK on hold: '{hold_id}' (Press 's' to skip, 'q' to quit)"
        cv2.putText(temp_img, prompt, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        while click_coords is None:
            cv2.imshow(window_name, temp_img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Quitting.")
                break
            elif key == ord('s'):
                print(f"Skipping hold '{hold_id}'.")
                click_coords = (-1, -1) # Sentinel to break inner loop
                break
        
        if click_coords == (-1, -1): # Skipped
            continue
        if key == ord('q'): # Quit
            break
            
        holds_data[hold_id] = {'x': click_coords[0], 'y': click_coords[1]}
        print(f"Added '{hold_id}' at {click_coords}")

    cv2.destroyAllWindows()

    # Save the updated holds data
    holds_path.parent.mkdir(parents=True, exist_ok=True)
    with open(holds_path, 'w', encoding='utf-8') as f:
        json.dump(holds_data, f, indent=4, sort_keys=True)
    
    print(f"\nUpdated holds data saved to '{holds_path}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactively add missing hold coordinates for a specific wall.")
    parser.add_argument("--wall_dir", required=True, help="Path to the wall directory (e.g., 'walls/spray_wall').")
    args = parser.parse_args()
    main(args.wall_dir)
