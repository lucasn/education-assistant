const MessageBubble = ({idx, message}) => {
    const [contextExpanded, setContextExpanded] = useState(false);
    const [toolCallExpanded, setToolCallExpanded] = useState(false);
    
    return (
        <div key={idx} className={`flex gap-4 ${message.type === 'human' ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${message.type === 'human'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100'
                    }`}
            >
                {
                    message.type == "tool" ?
                    <div>
                        <button
                            onClick={() => setToolCallExpanded(!toolCallExpanded)}
                            className="flex items-center gap-2 text-sm text-gray-300 hover:text-gray-100 transition-colors"
                        >
                            {toolCallExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
                            <span>Tool called: {message.name}</span>
                        </button>
                        
                        {toolCallExpanded && (
                            <div className="mt-2 p-3 bg-gray-700 rounded-lg text-sm text-gray-200 max-h-48 overflow-y-auto">
                                <p className="whitespace-pre-wrap">{message.content}</p>
                            </div>
                        )}
                    </div>
                    :
                    <div>
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        {message.type === 'ai' && message.additional_kwargs && message.additional_kwargs.context && (
                            <div className="mt-3 pt-3 border-t border-gray-600">
                                <button
                                    onClick={() => setContextExpanded(!contextExpanded)}
                                    className="flex items-center gap-2 text-sm text-gray-300 hover:text-gray-100 transition-colors"
                                >
                                    {contextExpanded ? <ChevronUpIcon /> : <ChevronDownIcon />}
                                    <span>Context</span>
                                </button>
                                
                                {contextExpanded && (
                                    <div className="mt-2 p-3 bg-gray-700 rounded-lg text-sm text-gray-200 max-h-48 overflow-y-auto">
                                        <p className="whitespace-pre-wrap">{message.additional_kwargs.context}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                }
                

            </div>
        </div>
    )
}