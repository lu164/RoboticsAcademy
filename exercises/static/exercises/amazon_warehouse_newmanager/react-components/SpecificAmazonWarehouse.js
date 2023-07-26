import * as React from "react";
import PropTypes from "prop-types";
import { draw } from "Helpers/BirdEye";

function SpecificAmazonWarehouse(props) {
  const guiCanvasRef = React.useRef();

  React.useEffect(() => {
    console.log("TestShowScreen subscribing to ['update'] events");
    
    const getMapDataAndDraw = (data) => {
      print("[Draw map] Data map: " + str(data.map))
      if (data.map) {
        const pose = data.map.substring(1, data.map.length - 1);
        const content = pose.split(',').map(function(item) {
          return parseFloat(item);
        })
        print("pose: " + str(pose))
        print("content: " + str(content))
        draw((content[0] ), (content[1] ), content[2], content[3]);
      }
    }
    const getPathAndDisplay = (data) => {
      print("[Draw path] Data array: " + str(data.array))
      if(data.array){
        generatePath(JSON.parse(data.array))
      }
    }

    const callback = (message) => {
      print("\n\n\n\nBIRD EYE -------------------------------")
      const data = message.data.update;
      print("[callback] Data: " + str(data))
      getMapDataAndDraw(data)
      getPathAndDisplay(data)
    };

    window.RoboticsExerciseComponents.commsManager.subscribe(
      [window.RoboticsExerciseComponents.commsManager.events.UPDATE],
      callback
    );

    return () => {
      console.log("TestShowScreen unsubscribing from ['state-changed'] events");
      window.RoboticsExerciseComponents.commsManager.unsubscribe(
        [window.RoboticsExerciseComponents.commsManager.events.UPDATE],
        callback
      );
    };
  }, []);

  return (
    <canvas
      ref={guiCanvasRef}
      style={{
        backgroundImage:
          "url('/static/exercises/amazon_warehouse_newmanager/resources/images/map.png')",
        border: "2px solid #d3d3d3",
        backgroundRepeat: "no-repeat",
        backgroundSize: "100% 100%",
        width: "100%",
        height: "100%"
      }}
    />
  );
}

SpecificAmazonWarehouse.propTypes = {
  circuit: PropTypes.string,
};

export default SpecificAmazonWarehouse
