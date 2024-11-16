function validateEmail(email) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
        return 'Por favor, insira um email para recuperação.';
    } else if (!emailPattern.test(email)) {
        return 'Por favor, insira um email válido.';
    }
    return '';
}

function sendRecoveryEmail(callback) {
    setTimeout(() => {
        callback();
    }, 500);
}

module.exports = { validateEmail, sendRecoveryEmail };
