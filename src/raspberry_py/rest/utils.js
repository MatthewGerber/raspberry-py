
element_id_call_time = {};
element_id_latency = {};
element_id_alpha = {};

function init_latency(element_id, alpha) {
  element_id_latency[element_id] = null;
  element_id_alpha[element_id] = alpha;
}

function set_call_time(element_id) {
  element_id_call_time[element_id] = Date.now()
}

function update_latency(element_id) {
    const latency = Date.now() - element_id_call_time[element_id];
    const alpha = element_id_alpha[element_id];
    let running_latency = element_id_latency[element_id];
    if (running_latency === null) {
      running_latency = latency;
    }
    else {
      running_latency = alpha * running_latency + (1.0 - alpha) * latency;
    }
    return running_latency;
}

async function is_checked(element) {
  while (!element.is(":checked")) {
    await new Promise(r => setTimeout(r, 1000));
  }
}