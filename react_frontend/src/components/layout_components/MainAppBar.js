import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Image from "mui-image";
import { Box, Typography } from "@mui/material";
import RoboticsTheme from "Components/RoboticsTheme.js";
import PropTypes from "prop-types";
import { ConnectionIndicator } from "Components/visualizers/ConnectionIndicator";
import { LaunchIndicator } from "Components/visualizers/LaunchIndicator";
import { useUnload } from "Hooks/useUnload";
import ExerciseTheoryForumButton from "../buttons/ExerciseTheoryForumButton";

function MainAppBar(props) {
  const serverBase = `${document.location.protocol}//${document.location.hostname}:8000`;
  let ros_version = 1;

  const fetchRosVersion = (data) => {
    // Requests ROS version and filters exercises by ROS tag
    const rosVersionURL = `${serverBase}/exercises/ros_version/`;
    fetch(rosVersionURL)
      .then((res) => res.json())
      .then((msg) => {
        ros_version = msg.version;
        // If ROS is not installed
        if (isNaN(parseInt(ros_version))) {
          ros_version = 1;
        }
      })
      .catch((error) => {
        ros_version = 1;
      });
  };

  const maxConnectionAttempts = 3;
  let connectionAttempts = 0;

  const connectWithRetry = () => {
    if (connectionAttempts >= maxConnectionAttempts) {
      RoboticsReactComponents.MessageSystem.Alert.showAlert(
        "Error conectando, prueba a recargar la página",
        () => {
          console.log("Reloading");
          window.location.reload();
        },
        "RECARGAR"
      );
      return;
    }

    window.RoboticsReactComponents.MessageSystem.Loading.showLoading(
      "Conectando y lanzando el ejercicio"
    );

    fetchRosVersion();
    window.RoboticsExerciseComponents.commsManager
      .connect()
      .then(() => {
        const config = JSON.parse(
          document.getElementById("exercise-config").textContent
        );
        // Selects the configs available for the ROS version installed
        const launchConfigs = {};
        let selectedConfig = {};
        launchConfigs[`ROS${ros_version}`] = config[`ROS${ros_version}`];
        if (launchConfigs.hasOwnProperty(`ROS${ros_version}`)) {
          if (Array.isArray(launchConfigs[`ROS${ros_version}`])) {
            selectedConfig = launchConfigs[`ROS${ros_version}`][0];
          } else {
            selectedConfig = launchConfigs[`ROS${ros_version}`];
          }
        } else {
          // Compatibility, if there is no ROS data, send the complete object
          selectedConfig = config;
        }
        selectedConfig["exercise_id"] = config["exercise_id"];
        window.RoboticsExerciseComponents.commsManager
          .launch(selectedConfig)
          .then(() => {
            RoboticsReactComponents.MessageSystem.Loading.hideLoading();
            RoboticsReactComponents.MessageSystem.Alert.showAlert(
              "Ejercicio cargado correctamente"
            );
          })
          .catch((e) => {
            RoboticsReactComponents.MessageSystem.Alert.showAlert(
              e.data.message
            );
          });
      })
      .catch((e) => {
        // Connection failed, try again after a delay
        connectionAttempts++;
        setTimeout(connectWithRetry, 2000);
      });
  };

  const disconnect = () => {
    window.RoboticsExerciseComponents.commsManager.disconnect();
  };

  React.useEffect(() => {
    RoboticsExerciseComponents.suscribeOnLoad(() => {
      connectWithRetry();
    });
  }, []);

  useUnload(() => {
    disconnect();
  });

  return (
    <RoboticsTheme>
      <AppBar position="relative">
        <Toolbar
          sx={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
          }}
        >
          <Box
            sx={{
              display: "inline-flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Image src="/static/common/img/logo.gif" fit={"cover"} width={50} />
            <Box
              sx={{
                display: "flex",
                gap: "10px",
                marginLeft: "10px",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <ConnectionIndicator></ConnectionIndicator>
              <LaunchIndicator></LaunchIndicator>
              {props.children}
            </Box>
          </Box>
          <Typography variant="h5">{props.exerciseName}</Typography>
          <Box>
            <ExerciseTheoryForumButton></ExerciseTheoryForumButton>
          </Box>
        </Toolbar>
      </AppBar>
    </RoboticsTheme>
  );
}

MainAppBar.propTypes = {
  exerciseName: PropTypes.string,
};

export default MainAppBar;
