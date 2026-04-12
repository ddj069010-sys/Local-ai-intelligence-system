import React from 'react';
import { Trash2, Plus, MessageSquare, Clock, Tag } from 'lucide-react';

const MemoryCard = ({ entry, onDelete, onAddToChat }) => {
    const formattedDate = new Date(entry.created_at || entry.timestamp).toLocaleString();

    return (
        <div className="bg-gray-800/50 border border-gray-700/50 hover:border-blue-500/50 rounded-xl p-5 transition-all group">
            <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-gray-100 group-hover:text-blue-400 transition-colors">
                    {entry.summary || entry.title || "Untitled Memory"}
                </h3>
                <div className="flex gap-1">
                    <button
                        onClick={() => onDelete(entry.id)}
                        className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                        title="Delete from memory"
                    >
                        <Trash2 size={16} />
                    </button>
                </div>
            </div>

            <div className="text-gray-300 text-sm leading-relaxed mb-4">
                {entry.key_points && entry.key_points.length > 0 ? (
                    <ul className="space-y-1 mb-3">
                        {entry.key_points.map((point, idx) => (
                            <li key={idx} className="flex gap-2 items-start text-xs text-gray-400">
                                <span className="text-blue-500 mt-1">•</span>
                                {point}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="line-clamp-3">{entry.content}</p>
                )}
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
                {entry.tags && entry.tags.map((tag, idx) => (
                    <span key={idx} className="flex items-center gap-1 px-2 py-1 bg-gray-700/50 text-gray-400 text-[10px] uppercase font-bold rounded-md">
                        <Tag size={10} /> {tag}
                    </span>
                ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-700/30">
                <div className="flex flex-col gap-1">
                    <span className="flex items-center gap-1.5 text-[9px] text-gray-500 uppercase tracking-wider font-bold">
                        <Clock size={10} /> {formattedDate}
                    </span>
                    <span className="flex items-center gap-1.5 text-[9px] text-gray-500 uppercase tracking-wider font-bold">
                        <MessageSquare size={10} /> {entry.chat_title || (entry.chat_id ? `Chat: ${entry.chat_id.slice(0, 8)}` : 'Manual Entry')}
                    </span>
                </div>

                <button
                    onClick={() => onAddToChat(entry.content)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-blue-600/10 text-blue-400 hover:bg-blue-600 hover:text-white rounded-lg text-[10px] font-bold uppercase transition-all"
                >
                    <Plus size={14} /> Add to Chat
                </button>
            </div>
        </div>
    );
};

export default MemoryCard;
