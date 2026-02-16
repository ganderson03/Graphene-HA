function createLeakingInterval(_input) {
    setInterval(() => {}, 1000);
    return 'ok';
}

function createLeakingTimeout(_input) {
    setTimeout(() => {}, 2000);
    return 'ok';
}

module.exports = {
    createLeakingInterval,
    createLeakingTimeout
};
