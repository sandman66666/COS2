"""
Intelligence API Routes
=====================
Enhanced API routes for intelligence features including multidimensional knowledge matrix
"""

import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel

from auth.auth_manager import get_current_user
from models.user import User
from utils.logging import structured_logger as logger
from intelligence.claude_analysis import KnowledgeTreeBuilder
from intelligence.knowledge_tree.multidimensional_matrix import MultidimensionalKnowledgeMatrix
from storage.storage_manager import get_storage_manager
from intelligence.ceo_strategic_intelligence_system import CEOStrategicIntelligenceSystem

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

# Initialize components
knowledge_tree_builder = KnowledgeTreeBuilder.get_instance()

class AnalysisRequest(BaseModel):
    """Request model for analysis operations"""
    time_window_days: int = 30
    analysis_types: List[str] = ["business", "relationships", "technical", "market", "predictive"]
    analysis_depth: str = "standard"  # standard, deep, multidimensional

class MatrixRequest(BaseModel):
    """Request model for multidimensional matrix building"""
    time_window_days: int = 30
    include_hierarchical: bool = True
    include_insights: bool = True

@router.post("/build-multidimensional-matrix")
async def build_multidimensional_matrix(
    request: MatrixRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Build a multidimensional knowledge matrix that creates deep worldview understanding.
    This goes far beyond simple categorization to understand how the user thinks about their world.
    """
    try:
        logger.info(f"Building multidimensional matrix for user {user.id}")
        
        # Create matrix builder
        matrix_builder = MultidimensionalKnowledgeMatrix(user.id)
        
        # Build the comprehensive matrix
        matrix = await matrix_builder.build_multidimensional_matrix(
            user_id=user.id,
            time_window_days=request.time_window_days
        )
        
        if matrix.get("error"):
            raise HTTPException(status_code=500, detail=matrix["error"])
        
        if matrix.get("status") == "no_data":
            return {
                "success": True,
                "message": "No email data available for analysis",
                "matrix": {},
                "recommendations": ["Sync more emails", "Extend time window"]
            }
        
        # Store the matrix
        storage_manager = await get_storage_manager()
        await storage_manager.store_knowledge_tree(user.id, matrix)
        
        # Generate summary for response
        matrix_summary = {
            "build_timestamp": matrix.get("matrix_metadata", {}).get("build_timestamp"),
            "time_window_days": request.time_window_days,
            "analysis_depth": "multidimensional",
            "components": list(matrix.keys()),
            "hierarchical_levels": len(matrix.get("hierarchical_structure", {})),
            "strategic_insights_count": len(matrix.get("strategic_insights", {}).get("key_insights", [])),
            "worldview_frameworks": len(matrix.get("core_worldview", {})),
            "cross_domain_connections": len(matrix.get("cross_domain_links", []))
        }
        
        return {
            "success": True,
            "message": "Multidimensional knowledge matrix built successfully",
            "matrix_summary": matrix_summary,
            "preview": {
                "core_philosophies": matrix.get("core_worldview", {}),
                "key_insights": matrix.get("strategic_insights", {}).get("key_insights", [])[:3],
                "thematic_structures": list(matrix.get("thematic_structures", {}).keys())
            }
        }
        
    except Exception as e:
        logger.error(f"Multidimensional matrix building error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/multidimensional-matrix")
async def get_multidimensional_matrix(
    user: User = Depends(get_current_user)
):
    """
    Get the user's multidimensional knowledge matrix.
    """
    try:
        storage_manager = await get_storage_manager()
        matrix = await storage_manager.get_knowledge_tree(user_id=user.id)
        
        if not matrix:
            return {
                "success": True,
                "message": "No multidimensional matrix found",
                "matrix": {},
                "recommendation": "Build matrix first using /build-multidimensional-matrix"
            }
        
        # Check if this is a multidimensional matrix
        is_multidimensional = (
            matrix.get("matrix_metadata", {}).get("analysis_depth") == "multidimensional" or
            "hierarchical_structure" in matrix or
            "strategic_insights" in matrix
        )
        
        return {
            "success": True,
            "matrix": matrix,
            "is_multidimensional": is_multidimensional,
            "last_updated": matrix.get("matrix_metadata", {}).get("build_timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error retrieving multidimensional matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-tree")
async def get_knowledge_tree(
    user: User = Depends(get_current_user)
):
    """
    Get the user's knowledge tree (personal knowledge graph).
    """
    try:
        storage_manager = await get_storage_manager()
        knowledge_tree = await storage_manager.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "Knowledge tree not found or not yet built",
                "knowledge_tree": {}
            }
        
        return {
            "success": True,
            "knowledge_tree": knowledge_tree
        }
    except Exception as e:
        logger.exception(f"Error retrieving knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/build-knowledge-tree")
async def build_knowledge_tree(
    request: AnalysisRequest,
    user: User = Depends(get_current_user)
):
    """
    Build knowledge tree using enhanced Claude analysts with worldview modeling.
    """
    try:
        logger.info(f"Building enhanced knowledge tree for user {user.id}")
        
        # Determine analysis approach based on depth
        if request.analysis_depth == "multidimensional":
            # Use the multidimensional matrix builder
            matrix_builder = MultidimensionalKnowledgeMatrix(user.id)
            knowledge_tree = await matrix_builder.build_multidimensional_matrix(
                user_id=user.id,
                time_window_days=request.time_window_days
            )
        else:
            # Use enhanced standard knowledge tree builder
            knowledge_tree = await knowledge_tree_builder.build_knowledge_tree(
                user_id=user.id,
                time_window_days=request.time_window_days
            )
        
        if not knowledge_tree:
            raise HTTPException(status_code=500, detail="Failed to build knowledge tree")
        
        if knowledge_tree.get("status") == "no_data":
            return {
                "success": True,
                "message": "No email data available for analysis",
                "knowledge_tree_summary": {},
                "recommendations": [
                    "Sync more emails using the email sync feature",
                    "Try extending the time window",
                    "Check that OAuth authentication is working"
                ]
            }
        
        if knowledge_tree.get("status") == "error":
            raise HTTPException(status_code=500, detail=knowledge_tree.get("error", "Unknown error"))
        
        # Generate comprehensive summary
        summary = {
            "time_window": knowledge_tree.get("time_window", {}),
            "analysis_type": request.analysis_depth,
            "build_timestamp": knowledge_tree.get("matrix_metadata", {}).get("build_timestamp") or knowledge_tree.get("time_window", {}).get("analysis_timestamp")
        }
        
        if request.analysis_depth == "multidimensional":
            summary.update({
                "worldview_components": len(knowledge_tree.get("core_worldview", {})),
                "strategic_insights": len(knowledge_tree.get("strategic_insights", {}).get("key_insights", [])),
                "cross_domain_connections": len(knowledge_tree.get("cross_domain_links", [])),
                "hierarchical_levels": len(knowledge_tree.get("hierarchical_structure", {}))
            })
        else:
            summary.update({
                "insight_count": sum(len(insights) for insights in knowledge_tree.get("insights", {}).values()) if knowledge_tree.get("insights") else 0,
                "relationship_count": len(knowledge_tree.get("relationships", [])),
                "topic_count": len(knowledge_tree.get("topics", [])),
                "entity_count": len(knowledge_tree.get("entities", []))
            })
        
        return {
            "success": True,
            "message": f"Enhanced knowledge tree successfully built with {request.analysis_depth} analysis",
            "knowledge_tree_summary": summary,
            "preview": {
                "key_insights": self._extract_preview_insights(knowledge_tree, request.analysis_depth),
                "main_themes": self._extract_main_themes(knowledge_tree, request.analysis_depth)
            }
        }
        
    except Exception as e:
        logger.exception(f"Error building knowledge tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _extract_preview_insights(knowledge_tree: Dict, analysis_depth: str) -> List[str]:
    """Extract preview insights from knowledge tree"""
    insights = []
    
    if analysis_depth == "multidimensional":
        strategic_insights = knowledge_tree.get("strategic_insights", {}).get("key_insights", [])
        insights.extend([insight.get("summary", str(insight))[:200] for insight in strategic_insights[:3]])
        
        # Add worldview insights
        worldview = knowledge_tree.get("core_worldview", {})
        for key, value in worldview.items():
            if isinstance(value, str):
                insights.append(f"{key}: {value[:150]}...")
                if len(insights) >= 5:
                    break
    else:
        # Extract from standard analysis
        for analyst_type, analyst_insights in knowledge_tree.get("insights", {}).items():
            if isinstance(analyst_insights, dict):
                for insight_key, insight_value in analyst_insights.items():
                    if isinstance(insight_value, str) and len(insight_value) > 50:
                        insights.append(f"{analyst_type} - {insight_key}: {insight_value[:150]}...")
                        if len(insights) >= 5:
                            break
    
    return insights[:5]

def _extract_main_themes(knowledge_tree: Dict, analysis_depth: str) -> List[str]:
    """Extract main themes from knowledge tree"""
    themes = []
    
    if analysis_depth == "multidimensional":
        thematic_structures = knowledge_tree.get("thematic_structures", {})
        themes.extend(list(thematic_structures.keys())[:10])
        
        # Add hierarchical structure themes
        hierarchical = knowledge_tree.get("hierarchical_structure", {})
        themes.extend(list(hierarchical.keys())[:5])
    else:
        # Extract from standard topics
        topics = knowledge_tree.get("topics", [])
        themes.extend(topics[:10])
        
        # Extract from analyst insights
        for analyst_type, insights in knowledge_tree.get("insights", {}).items():
            themes.append(analyst_type.replace("_", " ").title())
    
    return list(set(themes))[:10]

@router.get("/analysis-status")
async def get_analysis_status(
    user: User = Depends(get_current_user)
):
    """
    Get the status of knowledge analysis for the user.
    """
    try:
        storage_manager = await get_storage_manager()
        knowledge_tree = await storage_manager.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "status": "no_analysis",
                "message": "No knowledge analysis found",
                "recommendations": ["Build knowledge tree or multidimensional matrix"]
            }
        
        # Determine analysis type and status
        is_multidimensional = (
            knowledge_tree.get("matrix_metadata", {}).get("analysis_depth") == "multidimensional" or
            "hierarchical_structure" in knowledge_tree
        )
        
        last_updated = (
            knowledge_tree.get("matrix_metadata", {}).get("build_timestamp") or
            knowledge_tree.get("time_window", {}).get("analysis_timestamp")
        )
        
        return {
            "success": True,
            "status": "completed",
            "analysis_type": "multidimensional" if is_multidimensional else "standard",
            "last_updated": last_updated,
            "components_available": list(knowledge_tree.keys()),
            "data_quality": {
                "has_insights": bool(knowledge_tree.get("insights") or knowledge_tree.get("strategic_insights")),
                "has_relationships": bool(knowledge_tree.get("relationships")),
                "has_worldview": bool(knowledge_tree.get("core_worldview")),
                "has_hierarchy": bool(knowledge_tree.get("hierarchical_structure"))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/strategic")
async def get_strategic_insights(
    user: User = Depends(get_current_user)
):
    """
    Get strategic insights from the knowledge analysis.
    """
    try:
        storage_manager = await get_storage_manager()
        knowledge_tree = await storage_manager.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "No knowledge analysis found",
                "insights": []
            }
        
        # Extract strategic insights
        strategic_insights = knowledge_tree.get("strategic_insights", {})
        
        if not strategic_insights:
            # Try to extract from standard analysis
            insights = knowledge_tree.get("insights", {})
            strategic_insights = {
                "key_insights": [],
                "opportunities": [],
                "recommendations": []
            }
            
            for analyst_type, analyst_insights in insights.items():
                if isinstance(analyst_insights, dict):
                    for key, value in analyst_insights.items():
                        if any(keyword in key.lower() for keyword in ["insight", "opportunity", "recommendation", "strategic"]):
                            if isinstance(value, list):
                                strategic_insights["key_insights"].extend(value)
                            elif isinstance(value, str):
                                strategic_insights["key_insights"].append({"content": value, "source": f"{analyst_type}.{key}"})
        
        return {
            "success": True,
            "strategic_insights": strategic_insights,
            "worldview_summary": knowledge_tree.get("core_worldview", {}),
            "cross_domain_connections": knowledge_tree.get("cross_domain_links", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting strategic insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hierarchy")
async def get_knowledge_hierarchy(
    user: User = Depends(get_current_user)
):
    """
    Get the hierarchical structure of the knowledge matrix for navigation.
    """
    try:
        storage_manager = await get_storage_manager()
        knowledge_tree = await storage_manager.get_knowledge_tree(user_id=user.id)
        
        if not knowledge_tree:
            return {
                "success": True,
                "message": "No knowledge analysis found",
                "hierarchy": {}
            }
        
        hierarchical_structure = knowledge_tree.get("hierarchical_structure", {})
        
        if not hierarchical_structure:
            # Create a basic hierarchy from available data
            hierarchy = {}
            
            # From insights
            insights = knowledge_tree.get("insights", {})
            for analyst_type, analyst_insights in insights.items():
                hierarchy[analyst_type] = {
                    "subcategories": {},
                    "content": f"Analysis from {analyst_type.replace('_', ' ').title()}",
                    "type": "analyst_output"
                }
                
                if isinstance(analyst_insights, dict):
                    for key, value in analyst_insights.items():
                        hierarchy[analyst_type]["subcategories"][key] = {
                            "content": str(value)[:200] if isinstance(value, str) else str(value),
                            "type": "insight"
                        }
            
            hierarchical_structure = hierarchy
        
        return {
            "success": True,
            "hierarchy": hierarchical_structure,
            "navigation_levels": len(hierarchical_structure),
            "total_nodes": sum(len(domain.get("subcategories", {})) for domain in hierarchical_structure.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge hierarchy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild")
async def rebuild_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Rebuild the knowledge analysis with new parameters.
    """
    try:
        logger.info(f"Rebuilding knowledge analysis for user {user.id} with depth: {request.analysis_depth}")
        
        # Clear existing analysis
        storage_manager = await get_storage_manager()
        await storage_manager.store_knowledge_tree(user.id, {})
        
        # Rebuild with new parameters
        if request.analysis_depth == "multidimensional":
            matrix_builder = MultidimensionalKnowledgeMatrix(user.id)
            result = await matrix_builder.build_multidimensional_matrix(
                user_id=user.id,
                time_window_days=request.time_window_days
            )
        else:
            result = await knowledge_tree_builder.build_knowledge_tree(
                user_id=user.id,
                time_window_days=request.time_window_days
            )
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "message": f"Knowledge analysis rebuilt with {request.analysis_depth} depth",
            "analysis_type": request.analysis_depth,
            "time_window_days": request.time_window_days
        }
        
    except Exception as e:
        logger.error(f"Error rebuilding analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ceo-intelligence-brief")
async def generate_ceo_intelligence_brief(request: Request):
    """Generate comprehensive CEO intelligence brief"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1  # Default for development
        
        # Get request parameters
        body = await request.json() if request.headers.get("content-length") else {}
        focus_area = body.get('focus_area')
        priority_objectives = body.get('priority_objectives', [])
        
        # Initialize CEO Strategic Intelligence System
        ceo_system = CEOStrategicIntelligenceSystem(
            user_id=user_id,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        # Generate comprehensive intelligence brief
        brief = await ceo_system.generate_ceo_intelligence_brief(
            focus_area=focus_area,
            priority_objectives=priority_objectives
        )
        
        # Store the brief
        storage_manager = await get_storage_manager()
        # Note: These storage methods would need to be implemented
        # await storage_manager.store_ceo_intelligence_brief(user_id, brief)
        
        logger.info(
            "CEO intelligence brief generated successfully",
            user_id=user_id,
            focus_area=focus_area,
            brief_sections=list(brief.keys()) if isinstance(brief, dict) else []
        )
        
        return {
            "status": "success",
            "message": "CEO intelligence brief generated successfully",
            "brief": brief,
            "analysis_timestamp": brief.get("analysis_timestamp") if isinstance(brief, dict) else None
        }
        
    except Exception as e:
        logger.error(f"Error generating CEO intelligence brief: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate CEO intelligence brief: {str(e)}")

@router.post("/strategic-contact-analysis/{contact_id}")
async def analyze_strategic_contact(contact_id: str):
    """Generate strategic analysis for a specific contact"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1
        
        # Initialize CEO Strategic Intelligence System
        ceo_system = CEOStrategicIntelligenceSystem(
            user_id=user_id,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        # Generate strategic contact analysis
        analysis = await ceo_system.analyze_strategic_contact(contact_id)
        
        # Store the analysis
        storage_manager = await get_storage_manager()
        # await storage_manager.store_strategic_contact_analysis(user_id, contact_id, analysis)
        
        logger.info(
            "Strategic contact analysis completed",
            user_id=user_id,
            contact_id=contact_id,
            analysis_success=not analysis.get("error")
        )
        
        return {
            "status": "success",
            "message": "Strategic contact analysis completed",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing strategic contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze strategic contact: {str(e)}")

@router.post("/decision-support")
async def generate_decision_support(request: Request):
    """Generate strategic decision support"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1
        
        # Get request data
        data = await request.json()
        decision_area = data.get('decision_area')
        decision_options = data.get('decision_options', [])
        
        if not decision_area:
            raise HTTPException(status_code=400, detail="Decision area is required")
        
        # Initialize CEO Strategic Intelligence System
        ceo_system = CEOStrategicIntelligenceSystem(
            user_id=user_id,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        # Generate decision support
        decision_support = await ceo_system.generate_decision_support(
            decision_area=decision_area,
            decision_options=decision_options
        )
        
        # Store the decision support
        storage_manager = await get_storage_manager()
        # await storage_manager.store_decision_support(user_id, decision_area, decision_support)
        
        logger.info(
            "Decision support generated",
            user_id=user_id,
            decision_area=decision_area,
            options_count=len(decision_options)
        )
        
        return {
            "status": "success",
            "message": "Decision support generated successfully",
            "decision_support": decision_support
        }
        
    except Exception as e:
        logger.error(f"Error generating decision support: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate decision support: {str(e)}")

@router.post("/network-to-objectives-mapping")
async def map_network_to_objectives():
    """Generate network-to-objectives mapping"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1
        
        # Initialize CEO Strategic Intelligence System
        ceo_system = CEOStrategicIntelligenceSystem(
            user_id=user_id,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        # Generate network mapping
        network_mapping = await ceo_system.map_network_to_objectives()
        
        # Store the network mapping
        storage_manager = await get_storage_manager()
        # await storage_manager.store_network_mapping(user_id, network_mapping)
        
        logger.info(
            "Network-to-objectives mapping completed",
            user_id=user_id,
            contacts_analyzed=network_mapping.get("total_contacts_analyzed", 0),
            objectives_mapped=network_mapping.get("objectives_mapped", 0)
        )
        
        return {
            "status": "success",
            "message": "Network-to-objectives mapping completed",
            "network_mapping": network_mapping
        }
        
    except Exception as e:
        logger.error(f"Error mapping network to objectives: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to map network to objectives: {str(e)}")

@router.post("/competitive-landscape-analysis")
async def analyze_competitive_landscape():
    """Generate competitive landscape analysis"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1
        
        # Initialize competitive landscape analyst directly
        from intelligence.analysts.competitive_landscape_analyst import CompetitiveLandscapeAnalyst
        
        landscape_analyst = CompetitiveLandscapeAnalyst(
            user_id=user_id,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
        
        # Get data for analysis
        storage_manager = await get_storage_manager()
        contacts = await storage_manager.get_contacts_by_user(user_id)
        
        # Prepare analysis data
        analysis_data = {
            "company_context": {
                "name": "Session42",
                "industry": "AI Music Technology",
                "stage": "Growth Stage Startup",
                "products": "AI Music Creation Platform (HitCraft)",
                "competitive_position": "Artist-centric AI music tools"
            },
            "industry_context": {
                "market_size": "$1.2B AI music creation market",
                "growth_rate": "43% YoY growth",
                "key_trends": "AI democratization, creator economy growth"
            },
            "contact_network": contacts,
            "business_objectives": [
                {
                    "title": "Scale User Base to 100K Active Users",
                    "timeline": "Q3-Q4 2024",
                    "priority": "High"
                },
                {
                    "title": "Series B Funding Round", 
                    "timeline": "Q2 2024",
                    "priority": "High"
                }
            ]
        }
        
        # Generate competitive analysis
        landscape_analysis = await landscape_analyst.generate_intelligence(analysis_data)
        
        # Store the analysis
        # await storage_manager.store_competitive_landscape_analysis(user_id, landscape_analysis)
        
        logger.info(
            "Competitive landscape analysis completed",
            user_id=user_id,
            analysis_success=not landscape_analysis.get("error")
        )
        
        return {
            "status": "success",
            "message": "Competitive landscape analysis completed",
            "analysis": landscape_analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing competitive landscape: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze competitive landscape: {str(e)}")

@router.get("/ceo-intelligence-status")
async def get_ceo_intelligence_status():
    """Get status of CEO intelligence analyses"""
    try:
        # Get user ID (would come from authentication in production)
        user_id = 1
        
        # Get storage manager
        storage_manager = await get_storage_manager()
        
        # Check for existing analyses (these methods would need to be implemented)
        status = {
            "ceo_intelligence_brief": False,  # await storage_manager.has_ceo_intelligence_brief(user_id),
            "competitive_landscape": False,   # await storage_manager.has_competitive_landscape_analysis(user_id),
            "network_mapping": False,         # await storage_manager.has_network_mapping(user_id),
            "strategic_contacts": 0,          # await storage_manager.count_strategic_contact_analyses(user_id),
            "decision_support": 0,            # await storage_manager.count_decision_support_analyses(user_id),
            "last_analysis_timestamp": None   # await storage_manager.get_last_ceo_analysis_timestamp(user_id)
        }
        
        return {
            "status": "success",
            "intelligence_status": status
        }
        
    except Exception as e:
        logger.error(f"Error getting CEO intelligence status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get intelligence status: {str(e)}")
