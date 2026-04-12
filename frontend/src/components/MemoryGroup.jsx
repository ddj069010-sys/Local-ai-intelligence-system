import React from 'react';
import MemoryCard from './MemoryCard';
import { MessageSquare } from 'lucide-react';

const MemoryGroup = ({ title, entries, onDelete, onAddToChat }) => {
    return (
        <div className="mb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-3 mb-6 pb-2 border-b border-gray-800">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                    <MessageSquare size={20} />
                </div>
                <h2 className="text-xl font-bold text-gray-100">{title || "General Memories"}</h2>
                <span className="px-2 py-0.5 bg-gray-800 text-gray-500 text-[10px] font-bold rounded-full uppercase tracking-wider">
                    {entries.length} Entries
                </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {entries.map(entry => (
                    <MemoryCard 
                        key={entry.id} 
                        entry={entry} 
                        onDelete={onDelete}
                        onAddToChat={onAddToChat}
                    />
                ))}
            </div>
        </div>
    );
};

export default MemoryGroup;
