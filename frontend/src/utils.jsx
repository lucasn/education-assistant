export const handleKeyPress = (e, functionToCall) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        functionToCall();
    }
};
