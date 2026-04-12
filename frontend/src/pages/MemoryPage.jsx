import React, { useState, useEffect } from 'react';
import { Search, Plus, Loader2, Brain, X, Info } from 'lucide-react';
import { fetchMemoryEntries, deleteMemoryEntry, addMemoryEntry, searchMemory } from '../services/memoryApi';
import MemoryCard from '../components/MemoryCard';
import MemoryGroup from '../components/MemoryGroup';

const MemoryPage = () => {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [isAddOpen, setIsAddOpen] = useState(false);
    const [newEntry, setNewEntry] = useState({ title: '', content: '', tags: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        loadEntries();
    }, []);

    const loadEntries = async () => {
        setLoading(true);
        const data = await fetchMemoryEntries();
        setEntries(data);
        setLoading(false);
    };

    const handleSearch = async (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        if (query.trim()) {
            const results = await searchMemory(query);
            setEntries(results);
        } else {
            loadEntries();
        }
    };

    const handleDelete = async (id) => {
        const result = await deleteMemoryEntry(id);
        if (result && result.status === 'deleted') {
            setEntries(prev => prev.filter(e => e.id !== id));
        } else {
            console.error("Failed to delete memory:", result);
            alert("Error deleting memory. Ensure the backend is running.");
        }
    };

    const handleAddSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        const entry = {
            ...newEntry,
            tags: newEntry.tags.split(',').map(t => t.trim()).filter(t => t)
        };
        const result = await addMemoryEntry(entry);
        if (result.status === 'added') {
            setEntries([result.entry, ...entries]);
            setNewEntry({ title: '', content: '', tags: '' });
            setIsAddOpen(false);
        }
        setIsSubmitting(false);
    };

    const handleAddToChat = (content) => {
        // This is a placeholder for future state integration with the active chat
        alert('Prompting current chat with: ' + content);
    };

    // Correctly group entries by chat_title
    const groupedEntries = entries.reduce((acc, current) => {
        const title = current.chat_title || "Manual Entries";
        if (!acc[title]) acc[title] = [];
        acc[title].push(current);
        return acc;
    }, {});

    return (
        <div className="flex-1 overflow-y-auto bg-gray-900 text-gray-100 p-8">
            <div className="max-w-6xl mx-auto">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <Brain className="text-blue-500" size={32} />
                            <h1 className="text-4xl font-bold tracking-tight">Memory Pool</h1>
                        </div>
                        <p className="text-gray-400">Manage and search your cross-conversation knowledge.</p>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
                            <input 
                                type="text"
                                placeholder="Search memories or tags..."
                                value={searchQuery}
                                onChange={handleSearch}
                                className="w-64 pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                            />
                        </div>
                        <button 
                            onClick={() => setIsAddOpen(true)}
                            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20"
                        >
                            <Plus size={20} /> Add Entry
                        </button>
                    </div>
                </header>

                {isAddOpen && (
                    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className="bg-gray-800 border border-gray-700 rounded-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200">
                            <div className="bg-gray-900/50 p-6 border-b border-gray-700 flex justify-between items-center">
                                <h2 className="text-xl font-bold">New Memory Entry</h2>
                                <button onClick={() => setIsAddOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                                    <X size={24} />
                                </button>
                            </div>
                            <form onSubmit={handleAddSubmit} className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Title</label>
                                    <input 
                                        required
                                        value={newEntry.title}
                                        onChange={e => setNewEntry({...newEntry, title: e.target.value})}
                                        className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                                        placeholder="Brief title..."
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Content</label>
                                    <textarea 
                                        required
                                        rows={4}
                                        value={newEntry.content}
                                        onChange={e => setNewEntry({...newEntry, content: e.target.value})}
                                        className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                                        placeholder="Full knowledge or snippet..."
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Tags</label>
                                    <input 
                                        value={newEntry.tags}
                                        onChange={e => setNewEntry({...newEntry, tags: e.target.value})}
                                        className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                                        placeholder="code, react, api (comma separated)"
                                    />
                                </div>
                                <div className="pt-4 flex gap-3">
                                    <button 
                                        type="button"
                                        onClick={() => setIsAddOpen(false)}
                                        className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 text-white font-bold rounded-xl transition-all"
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:opacity-50 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                                    >
                                        {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : 'Save Entry'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 gap-4">
                        <Loader2 className="text-blue-500 animate-spin" size={48} />
                        <p className="text-gray-500 animate-pulse">Syncing memory pool...</p>
                    </div>
                ) : Object.keys(groupedEntries).length > 0 ? (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {Object.entries(groupedEntries).map(([title, items]) => (
                            <MemoryGroup 
                                key={title}
                                title={title}
                                entries={items}
                                onDelete={handleDelete}
                                onAddToChat={handleAddToChat}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center p-20 bg-gray-800/20 border-2 border-dashed border-gray-700 rounded-3xl gap-4">
                        <div className="p-4 bg-gray-800 rounded-full text-gray-500">
                            <Brain size={48} />
                        </div>
                        <div className="text-center">
                            <h3 className="text-xl font-bold mb-1">No Memories Found</h3>
                            <p className="text-gray-500">Your knowledge pool is empty or no matches were found.</p>
                        </div>
                        <button 
                            onClick={() => setIsAddOpen(true)}
                            className="mt-2 text-blue-400 hover:text-blue-300 font-semibold transition-all"
                        >
                            Add your first entry
                        </button>
                    </div>
                )}

                <footer className="mt-16 pt-8 border-t border-gray-800 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/5 text-blue-500/60 text-xs rounded-full border border-blue-500/10">
                        <Info size={14} /> Knowledge from your chats automatically syncs here.
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default MemoryPage;
