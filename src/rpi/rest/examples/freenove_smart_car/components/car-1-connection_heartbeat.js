async function car_1_connection_heartbeat() {
  $.ajax({
    url: "http://10.0.0.59:5000/call/car-1/connection_heartbeat",
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
await car_1_connection_heartbeat();
