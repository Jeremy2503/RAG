"""
Script to generate an architecture diagram for the Multi-Agent RAG System.
Creates a visual diagram showing all components and their relationships.
"""

from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch
import numpy as np

def create_architecture_diagram():
    """Create a comprehensive architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Define colors
    frontend_color = '#8B5CF6'  # Purple
    backend_color = '#3B82F6'  # Blue
    agent_color = '#10B981'     # Green
    db_color = '#F59E0B'        # Orange
    external_color = '#EF4444'  # Red
    bg_color = '#1E1E2E'        # Dark background
    
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    # Title
    title = ax.text(8, 11.5, 'Multi-Agent RAG System Architecture', 
                    ha='center', va='top', fontsize=20, fontweight='bold',
                    color='white', family='sans-serif')
    
    # ==================== FRONTEND LAYER ====================
    frontend_box = FancyBboxPatch((1, 9), 3, 1.5, 
                                   boxstyle="round,pad=0.1", 
                                   facecolor=frontend_color, 
                                   edgecolor='white', linewidth=2)
    ax.add_patch(frontend_box)
    ax.text(2.5, 10, 'Frontend\n(React)', ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    
    # Frontend components
    components = [
        ('User Dashboard', 1.2, 9.3),
        ('Chat Interface', 2.5, 9.3),
        ('Document Upload', 3.8, 9.3),
        ('Auth Pages', 2.5, 9.0)
    ]
    for comp, x, y in components:
        ax.text(x, y, f'• {comp}', fontsize=8, color='white', alpha=0.9)
    
    # ==================== API GATEWAY LAYER ====================
    api_box = FancyBboxPatch((6, 9), 3, 1.5,
                              boxstyle="round,pad=0.1",
                              facecolor=backend_color,
                              edgecolor='white', linewidth=2)
    ax.add_patch(api_box)
    ax.text(7.5, 10, 'API Gateway\n(FastAPI)', ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    
    # API endpoints
    endpoints = [
        ('/auth/*', 6.2, 9.3),
        ('/chat/*', 7.5, 9.3),
        ('/documents/*', 8.8, 9.3),
        ('/health', 7.5, 9.0)
    ]
    for endpoint, x, y in endpoints:
        ax.text(x, y, f'• {endpoint}', fontsize=8, color='white', alpha=0.9)
    
    # ==================== SERVICE LAYER ====================
    service_box = FancyBboxPatch((11, 9), 4, 1.5,
                                  boxstyle="round,pad=0.1",
                                  facecolor=backend_color,
                                  edgecolor='white', linewidth=2, alpha=0.8)
    ax.add_patch(service_box)
    ax.text(13, 10, 'Service Layer', ha='center', va='center',
            fontsize=12, fontweight='bold', color='white')
    
    services = [
        ('Auth Service', 11.2, 9.3),
        ('Chat Service', 12.5, 9.3),
        ('Document Service', 13.8, 9.3),
        ('Agent Service', 12.5, 9.0)
    ]
    for service, x, y in services:
        ax.text(x, y, f'• {service}', fontsize=8, color='white', alpha=0.9)
    
    # ==================== AGENT ORCHESTRATOR ====================
    orchestrator_box = FancyBboxPatch((1, 6.5), 14, 2,
                                       boxstyle="round,pad=0.15",
                                       facecolor=agent_color,
                                       edgecolor='white', linewidth=3)
    ax.add_patch(orchestrator_box)
    ax.text(8, 8, 'LangGraph Agent Orchestrator', ha='center', va='center',
            fontsize=14, fontweight='bold', color='white')
    
    # Coordinator
    coord_box = FancyBboxPatch((2, 6.8), 2.5, 1.2,
                               boxstyle="round,pad=0.1",
                               facecolor='#059669',
                               edgecolor='white', linewidth=2)
    ax.add_patch(coord_box)
    ax.text(3.25, 7.4, 'Coordinator\nAgent', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white')
    
    # Specialist Agents
    agents = [
        ('IT Policy\nAgent', 5.5, 7.4),
        ('HR Policy\nAgent', 8, 7.4),
        ('Research\nAgent', 10.5, 7.4)
    ]
    for i, (name, x, y) in enumerate(agents):
        agent_box = FancyBboxPatch((x-1, y-0.6), 2, 1.2,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#059669',
                                   edgecolor='white', linewidth=2)
        ax.add_patch(agent_box)
        ax.text(x, y, name, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')
    
    # Synthesis Node
    synth_box = FancyBboxPatch((13, 6.8), 1.5, 1.2,
                               boxstyle="round,pad=0.1",
                               facecolor='#059669',
                               edgecolor='white', linewidth=2)
    ax.add_patch(synth_box)
    ax.text(13.75, 7.4, 'Synthesis\nNode', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white')
    
    # Arrows in orchestrator
    # Coordinator to agents
    for x in [5.5, 8, 10.5]:
        arrow = FancyArrowPatch((4.75, 7.4), (x-1, 7.4),
                               arrowstyle='->', mutation_scale=20,
                               color='white', linewidth=2, alpha=0.7)
        ax.add_patch(arrow)
    
    # Agents to synthesis
    for x in [5.5, 8, 10.5]:
        arrow = FancyArrowPatch((x+1, 7.4), (13, 7.4),
                               arrowstyle='->', mutation_scale=20,
                               color='white', linewidth=2, alpha=0.7)
        ax.add_patch(arrow)
    
    # ==================== DATA ACCESS LAYER ====================
    # MongoDB Repository
    mongo_repo_box = FancyBboxPatch((1, 4), 3, 1.5,
                                    boxstyle="round,pad=0.1",
                                    facecolor=db_color,
                                    edgecolor='white', linewidth=2)
    ax.add_patch(mongo_repo_box)
    ax.text(2.5, 4.75, 'MongoDB\nRepository', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # ChromaDB Repository
    chroma_repo_box = FancyBboxPatch((5.5, 4), 3, 1.5,
                                      boxstyle="round,pad=0.1",
                                      facecolor=db_color,
                                      edgecolor='white', linewidth=2)
    ax.add_patch(chroma_repo_box)
    ax.text(7, 4.75, 'ChromaDB\nRepository', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # Embedding Generator
    embed_box = FancyBboxPatch((10, 4), 3, 1.5,
                               boxstyle="round,pad=0.1",
                               facecolor=backend_color,
                               edgecolor='white', linewidth=2, alpha=0.8)
    ax.add_patch(embed_box)
    ax.text(11.5, 4.75, 'Embedding\nGenerator', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    # ==================== PERSISTENCE LAYER ====================
    # MongoDB
    mongo_box = FancyBboxPatch((1, 1.5), 3, 1.5,
                               boxstyle="round,pad=0.1",
                               facecolor=db_color,
                               edgecolor='white', linewidth=2)
    ax.add_patch(mongo_box)
    ax.text(2.5, 2.25, 'MongoDB\n(Atlas)', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    mongo_data = ['Users', 'Chat History', 'Documents']
    for i, data in enumerate(mongo_data):
        ax.text(2.5, 1.7 + i*0.15, f'• {data}', fontsize=8, 
                color='white', alpha=0.9, ha='center')
    
    # ChromaDB
    chroma_box = FancyBboxPatch((5.5, 1.5), 3, 1.5,
                               boxstyle="round,pad=0.1",
                               facecolor=db_color,
                               edgecolor='white', linewidth=2)
    ax.add_patch(chroma_box)
    ax.text(7, 2.25, 'ChromaDB\n(Local)', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    chroma_data = ['Document Embeddings', 'Vector Search']
    for i, data in enumerate(chroma_data):
        ax.text(7, 1.7 + i*0.15, f'• {data}', fontsize=8,
                color='white', alpha=0.9, ha='center')
    
    # OpenAI
    openai_box = FancyBboxPatch((10, 1.5), 3, 1.5,
                                boxstyle="round,pad=0.1",
                                facecolor=external_color,
                                edgecolor='white', linewidth=2)
    ax.add_patch(openai_box)
    ax.text(11.5, 2.25, 'OpenAI API', ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    
    openai_services = ['GPT-4 (LLM)', 'Embeddings']
    for i, service in enumerate(openai_services):
        ax.text(11.5, 1.7 + i*0.15, f'• {service}', fontsize=8,
                color='white', alpha=0.9, ha='center')
    
    # Opik (optional)
    opik_box = FancyBboxPatch((14, 1.5), 1.5, 1.5,
                              boxstyle="round,pad=0.1",
                              facecolor=external_color,
                              edgecolor='white', linewidth=2, alpha=0.7)
    ax.add_patch(opik_box)
    ax.text(14.75, 2.25, 'Opik\n(Optional)', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    
    # ==================== ARROWS (Data Flow) ====================
    # Frontend to API Gateway
    arrow1 = FancyArrowPatch((4, 9.75), (6, 9.75),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=3)
    ax.add_patch(arrow1)
    ax.text(5, 10, 'HTTP/REST', ha='center', va='bottom',
            fontsize=9, color='white', style='italic')
    
    # API Gateway to Services
    arrow2 = FancyArrowPatch((9, 9.75), (11, 9.75),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=3)
    ax.add_patch(arrow2)
    
    # Services to Orchestrator
    arrow3 = FancyArrowPatch((7.5, 9), (8, 8.5),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=3)
    ax.add_patch(arrow3)
    
    # Orchestrator to Repositories
    arrow4 = FancyArrowPatch((3.25, 6.5), (2.5, 5.5),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2, alpha=0.7)
    ax.add_patch(arrow4)
    
    arrow5 = FancyArrowPatch((7, 6.5), (7, 5.5),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2, alpha=0.7)
    ax.add_patch(arrow5)
    
    arrow6 = FancyArrowPatch((11.5, 6.5), (11.5, 5.5),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2, alpha=0.7)
    ax.add_patch(arrow6)
    
    # Repositories to Databases
    arrow7 = FancyArrowPatch((2.5, 4), (2.5, 3),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2)
    ax.add_patch(arrow7)
    
    arrow8 = FancyArrowPatch((7, 4), (7, 3),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2)
    ax.add_patch(arrow8)
    
    # Embedding Generator to OpenAI
    arrow9 = FancyArrowPatch((11.5, 4), (11.5, 3),
                            arrowstyle='->', mutation_scale=25,
                            color='white', linewidth=2)
    ax.add_patch(arrow9)
    
    # Agents to OpenAI (for LLM)
    arrow10 = FancyArrowPatch((8, 6.5), (11.5, 3),
                              arrowstyle='->', mutation_scale=25,
                              color='white', linewidth=2, alpha=0.6,
                              connectionstyle="arc3,rad=0.3")
    ax.add_patch(arrow10)
    ax.text(10, 4.5, 'LLM Calls', ha='center', va='center',
            fontsize=8, color='white', alpha=0.8, rotation=-20)
    
    # ==================== LEGEND ====================
    legend_y = 0.5
    legend_items = [
        (frontend_color, 'Frontend Layer'),
        (backend_color, 'Backend Layer'),
        (agent_color, 'Agent System'),
        (db_color, 'Database'),
        (external_color, 'External Service')
    ]
    
    for i, (color, label) in enumerate(legend_items):
        rect = Rectangle((13.5 + i*0.6, legend_y), 0.3, 0.3,
                        facecolor=color, edgecolor='white', linewidth=1)
        ax.add_patch(rect)
        ax.text(13.5 + i*0.6 + 0.35, legend_y + 0.15, label,
                fontsize=8, color='white', va='center')
    
    # Save the diagram
    plt.tight_layout()
    output_path = 'Multi-Agent_RAG_Architecture_Diagram.png'
    plt.savefig(output_path, dpi=300, facecolor=bg_color, bbox_inches='tight',
                pad_inches=0.2)
    print(f"Architecture diagram generated successfully: {output_path}")
    
    # Also save as PDF for better quality
    output_path_pdf = 'Multi-Agent_RAG_Architecture_Diagram.pdf'
    plt.savefig(output_path_pdf, facecolor=bg_color, bbox_inches='tight',
                pad_inches=0.2)
    print(f"Architecture diagram (PDF) generated: {output_path_pdf}")
    
    return output_path, output_path_pdf

if __name__ == "__main__":
    create_architecture_diagram()

