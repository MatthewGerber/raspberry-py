import {rest_host, rest_port} from "./globals.js";
async function car_1_connection_heartbeat() {
  $.ajax({
    url: "http://" + rest_host + ":" + rest_port + "/call/car-1/connection_heartbeat",
    type: "GET",
    success: async function (_) {
      await new Promise(r => setTimeout(r, 500.0));
      await car_1_connection_heartbeat();
    },
    error: async function(xhr, error){
      console.log(error);
      await new Promise(r => setTimeout(r, 500.0));
      await car_1_connection_heartbeat();
    }
  });
}
car_1_connection_heartbeat();
