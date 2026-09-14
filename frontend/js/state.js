export function validateName(value) {
  const name = value.trim();
  const length = Array.from(name).length;
  return {
    name,
    length,
    valid: length >= 1 && length <= 10 && !/[\u0000-\u001f\u007f]/.test(name),
  };
}

export function createState() {
  let epoch = 0;
  const empty = () => ({
    screen: "home",
    flow: null,
    team: null,
    draftTeam: null,
    name: "",
    aiMode: null,
    capture: null,
    result: null,
    sessionId: null,
    nfc: "idle",
    printer: "idle",
    report: null,
    error: null,
    busy: false,
  });
  let data = empty();
  return {
    get data() {
      return data;
    },
    patch(values) {
      Object.assign(data, values);
    },
    reset() {
      epoch++;
      data = empty();
    },
    begin() {
      if (data.busy) return null;
      data.busy = true;
      return { epoch, screen: data.screen };
    },
    isCurrent(token) {
      return !!token && token.epoch === epoch && token.screen === data.screen;
    },
    finish(token) {
      if (!this.isCurrent(token)) return false;
      data.busy = false;
      return true;
    },
    invalidate() {
      epoch++;
      data.busy = false;
    },
  };
}
