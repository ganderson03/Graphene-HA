async function awaitShortTimeout(_input) {
    await new Promise(resolve => setTimeout(resolve, 10));
    return 'ok';
}

function clearIntervalSafely(_input) {
    const handle = setInterval(() => {}, 10);
    clearInterval(handle);
    return 'ok';
}

module.exports = {
    awaitShortTimeout,
    clearIntervalSafely
};
