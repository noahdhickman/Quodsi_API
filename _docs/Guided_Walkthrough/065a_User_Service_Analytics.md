# Step 6.5a: User Service Advanced Analytics

## Overview

This document extends the core UserService implementation with advanced analytics capabilities. It demonstrates how services can provide sophisticated business intelligence and user insights while maintaining clean architecture.

**Advanced Analytics Features:**
- User insights and personalized recommendations
- Tenant-level user management and analytics
- Engagement level calculations
- Usage pattern analysis
- Comprehensive user analytics methods

**Prerequisites:**
- Completed **065_User_Service_Implementation.md**
- Core UserService implemented and tested

---

## Step 1: Add Advanced Analytics Methods

### 1.1 Extend UserService with Analytics

Add these methods to your existing `app/services/user_service.py` file:

```python
# Add these methods to the existing UserService class

    # === Advanced Analytics ===
    
    def get_user_insights(self, tenant_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive user insights and recommendations.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to analyze
            
        Returns:
            Dictionary with detailed user insights or None if not found
        """
        activity_summary = self.get_user_activity_summary(tenant_id, user_id)
        if not activity_summary:
            return None
        
        # Generate usage patterns
        usage_patterns = self._analyze_usage_patterns(tenant_id, user_id)
        
        # Generate recommendations
        recommendations = self._generate_user_recommendations(activity_summary, usage_patterns)
        
        return {
            "user_id": str(user_id),
            "activity_summary": {
                "total_logins": activity_summary.total_logins,
                "total_usage_minutes": activity_summary.total_usage_minutes,
                "days_since_registration": activity_summary.days_since_registration,
                "engagement_level": activity_summary.engagement_level,
                "is_recently_active": activity_summary.is_recently_active
            },
            "usage_patterns": usage_patterns,
            "recommendations": recommendations
        }
    
    def _analyze_usage_patterns(self, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Analyze user usage patterns.
        
        Args:
            tenant_id: Tenant UUID for isolation
            user_id: User UUID to analyze
            
        Returns:
            Dictionary with usage pattern insights
        """
        stats = self.user_repo.get_user_statistics(self.db, tenant_id, user_id)
        
        return {
            "avg_session_length": stats.get("total_usage_minutes", 0) / max(stats.get("login_count", 1), 1),
            "login_frequency": "weekly" if stats.get("login_count", 0) > 0 else "never",
            "most_active_time": "business_hours",  # Would be calculated from actual session data
            "usage_trend": "stable"  # Would be calculated from historical data
        }
    
    def _generate_user_recommendations(self, activity_summary: UserActivitySummary, 
                                     usage_patterns: Dict[str, Any]) -> List[str]:
        """
        Generate personalized recommendations for the user.
        
        Args:
            activity_summary: User activity summary
            usage_patterns: User usage patterns
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if activity_summary.engagement_level == "low":
            recommendations.append("Try exploring more features to get the most value from the platform")
            recommendations.append("Consider setting up regular usage sessions to build engagement")
        
        if activity_summary.engagement_level == "inactive":
            recommendations.append("Welcome back! Check out what's new since your last visit")
            recommendations.append("Complete your profile setup to personalize your experience")
        
        if activity_summary.total_logins < 5:
            recommendations.append("Complete the getting started guide to learn key features")
        
        if usage_patterns["avg_session_length"] < 10:
            recommendations.append("Take time to explore features more deeply in each session")
        
        return recommendations
    
    # === Tenant-Level User Management ===
    
    def get_tenant_user_overview(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get overview of all users in a tenant for admin purposes.
        
        Args:
            tenant_id: Tenant UUID for isolation
            
        Returns:
            Dictionary with tenant user overview
        """
        try:
            # Get tenant user summary
            summary = self.user_repo.get_tenant_user_summary(self.db, tenant_id)
            
            # Get recent users
            recent_users = self.user_repo.get_users_by_status(
                self.db, tenant_id, "active", limit=10
            )
            
            # Calculate engagement distribution
            all_users = self.user_repo.get_all(self.db, tenant_id, limit=1000)
            engagement_distribution = self._calculate_engagement_distribution(tenant_id, all_users)
            
            return {
                "summary": summary,
                "recent_users": [{
                    "id": str(user.id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "status": user.status,
                    "last_login_at": user.last_login_at,
                    "created_at": user.created_at
                } for user in recent_users],
                "engagement_distribution": engagement_distribution
            }
            
        except Exception:
            return {
                "summary": {},
                "recent_users": [],
                "engagement_distribution": {}
            }
    
    def _calculate_engagement_distribution(self, tenant_id: UUID, users: List[User]) -> Dict[str, int]:
        """
        Calculate engagement level distribution for tenant users.
        
        Args:
            tenant_id: Tenant UUID for isolation
            users: List of users to analyze
            
        Returns:
            Dictionary with engagement level counts
        """
        distribution = {"high": 0, "medium": 0, "low": 0, "inactive": 0}
        
        for user in users:
            stats = self.user_repo.get_user_statistics(self.db, tenant_id, user.id)
            if stats:
                engagement_level = self._calculate_engagement_level(stats)
                distribution[engagement_level] += 1
        
        return distribution
    
    def get_tenant_user_analytics(self, tenant_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive tenant user analytics for specified period.
        
        Args:
            tenant_id: Tenant UUID for isolation
            days: Number of days to analyze
            
        Returns:
            Dictionary with tenant analytics
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get all users
            all_users = self.user_repo.get_all(self.db, tenant_id, limit=1000)
            
            # Calculate metrics
            total_users = len(all_users)
            active_users = len([u for u in all_users if u.status == "active"])
            
            # Calculate activity metrics
            total_logins = sum(u.login_count or 0 for u in all_users)
            total_usage = sum(getattr(u, 'total_usage_minutes', 0) or 0 for u in all_users)
            
            # Calculate averages
            avg_logins_per_user = total_logins / max(total_users, 1)
            avg_usage_per_user = total_usage / max(total_users, 1)
            
            return {
                "period_days": days,
                "total_users": total_users,
                "active_users": active_users,
                "total_logins": total_logins,
                "total_usage_minutes": total_usage,
                "avg_logins_per_user": round(avg_logins_per_user, 2),
                "avg_usage_per_user": round(avg_usage_per_user, 2),
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception:
            return {
                "period_days": days,
                "total_users": 0,
                "active_users": 0,
                "total_logins": 0,
                "total_usage_minutes": 0,
                "avg_logins_per_user": 0,
                "avg_usage_per_user": 0,
                "analysis_date": datetime.now(timezone.utc).isoformat()
            }
```

---

## Step 2: Understanding Analytics Features

### 2.1 User Insights Generation

**Complete Insights Flow**:
```python
def get_user_insights(self, tenant_id: UUID, user_id: UUID):
    # 1. Get activity summary (from basic service)
    # 2. Analyze usage patterns (advanced analytics)
    # 3. Generate personalized recommendations (business logic)
    # 4. Return comprehensive insights package
```

**Key Components**:
- **Activity Summary**: Login counts, usage time, engagement level
- **Usage Patterns**: Session length, frequency, timing preferences
- **Recommendations**: Personalized suggestions based on behavior

### 2.2 Engagement Level Calculation

**Engagement Algorithm**:
```python
def _calculate_engagement_level(self, user_stats: Dict[str, Any]) -> str:
    # Factors considered:
    # - Recent activity (is_recently_active)
    # - Login frequency (logins per day since registration)
    # - Usage intensity (usage minutes per day)
    # - Time since registration (contextualizes other metrics)
    
    # Returns: "high", "medium", "low", or "inactive"
```

**Engagement Levels**:
- **High**: >= 1 login/day AND >= 30 minutes/day usage
- **Medium**: >= 0.3 logins/day AND >= 10 minutes/day usage
- **Low**: Some activity but below medium thresholds
- **Inactive**: No recent activity (> 7 days)

### 2.3 Tenant-Level Analytics

**Organizational Insights**:
```python
def get_tenant_user_analytics(self, tenant_id: UUID, days: int = 30):
    # Provides organization-wide metrics:
    # - Total and active user counts
    # - Aggregate login and usage statistics
    # - Average engagement per user
    # - Trend analysis over specified period
```

---

## Step 3: Performance Considerations

### 3.1 Analytics Optimization

**Efficient User Queries**:
```python
# Use repository methods with proper limits
all_users = self.user_repo.get_all(self.db, tenant_id, limit=1000)

# For very large tenants, consider pagination:
def get_large_tenant_analytics(self, tenant_id: UUID):
    total_metrics = {"logins": 0, "usage": 0, "users": 0}
    
    for offset in range(0, 10000, 100):  # Process in batches of 100
        batch_users = self.user_repo.get_all(
            self.db, tenant_id, skip=offset, limit=100
        )
        if not batch_users:
            break
            
        # Process batch and accumulate metrics
        for user in batch_users:
            total_metrics["logins"] += user.login_count or 0
            total_metrics["usage"] += getattr(user, 'total_usage_minutes', 0) or 0
            total_metrics["users"] += 1
    
    return total_metrics
```

### 3.2 Caching Strategy

**Analytics Caching**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache insights for 1 hour (would use Redis in production)
@lru_cache(maxsize=100)
def get_cached_tenant_analytics(tenant_id: str, days: int, cache_key: str) -> Dict[str, Any]:
    """Cache tenant analytics with hourly expiration"""
    return self.get_tenant_user_analytics(UUID(tenant_id), days)

# Generate cache key with hour precision for auto-expiration
def get_analytics_cache_key() -> str:
    return datetime.now().strftime("%Y%m%d%H")  # Changes every hour
```

### 3.3 Database Query Optimization

**Efficient Engagement Calculation**:
```python
# Instead of loading full user objects for engagement distribution:
def _calculate_engagement_distribution_optimized(self, tenant_id: UUID) -> Dict[str, int]:
    """Optimized engagement calculation using direct queries"""
    
    # Use repository's efficient query methods
    stats_summary = self.user_repo.get_tenant_user_summary(self.db, tenant_id)
    
    # Calculate engagement based on aggregate statistics rather than individual users
    return {
        "high": stats_summary.get("highly_engaged_users", 0),
        "medium": stats_summary.get("moderately_engaged_users", 0),
        "low": stats_summary.get("low_engaged_users", 0),
        "inactive": stats_summary.get("inactive_users", 0)
    }
```

---

## Step 4: Usage Patterns and Examples

### 4.1 Dashboard Analytics

```python
# Example: Building analytics for admin dashboard
def get_admin_dashboard_analytics(db: Session, tenant_id: UUID):
    """Get comprehensive analytics for admin dashboard"""
    user_service = UserService(db)
    
    # Get overview and analytics
    overview = user_service.get_tenant_user_overview(tenant_id)
    analytics_30d = user_service.get_tenant_user_analytics(tenant_id, days=30)
    analytics_7d = user_service.get_tenant_user_analytics(tenant_id, days=7)
    
    return {
        "current_state": overview,
        "monthly_trends": analytics_30d,
        "weekly_trends": analytics_7d,
        "growth_rate": calculate_growth_rate(analytics_30d, analytics_7d)
    }

def calculate_growth_rate(monthly: Dict, weekly: Dict) -> float:
    """Calculate user growth rate"""
    monthly_avg_daily = monthly["total_logins"] / 30
    weekly_avg_daily = weekly["total_logins"] / 7
    
    if monthly_avg_daily > 0:
        return round(((weekly_avg_daily - monthly_avg_daily) / monthly_avg_daily) * 100, 2)
    return 0.0
```

### 4.2 User Personalization

```python
# Example: Personalized user experience
def get_personalized_experience(db: Session, tenant_id: UUID, user_id: UUID):
    """Get personalized user experience data"""
    user_service = UserService(db)
    
    # Get user insights
    insights = user_service.get_user_insights(tenant_id, user_id)
    if not insights:
        return {"error": "User insights not available"}
    
    # Customize experience based on engagement level
    engagement_level = insights["activity_summary"]["engagement_level"]
    
    if engagement_level == "high":
        experience = {
            "welcome_message": "Welcome back! You're one of our most active users.",
            "suggested_features": ["Advanced Analytics", "API Integration", "Custom Reports"],
            "priority_support": True
        }
    elif engagement_level == "medium":
        experience = {
            "welcome_message": "Great to see you again!",
            "suggested_features": ["Feature Tour", "Productivity Tips", "Community Forums"],
            "priority_support": False
        }
    else:  # low or inactive
        experience = {
            "welcome_message": "Let's get you started with the basics.",
            "suggested_features": ["Getting Started Guide", "Basic Tutorial", "Help Center"],
            "priority_support": False
        }
    
    experience["recommendations"] = insights["recommendations"]
    return experience
```

### 4.3 Automated Insights

```python
# Example: Automated insight generation for regular reports
def generate_weekly_insights_report(db: Session, tenant_id: UUID):
    """Generate automated weekly insights report"""
    user_service = UserService(db)
    
    # Get analytics for the week
    weekly_analytics = user_service.get_tenant_user_analytics(tenant_id, days=7)
    overview = user_service.get_tenant_user_overview(tenant_id)
    
    # Generate insights
    insights = []
    
    # Engagement insights
    engagement_dist = overview["engagement_distribution"]
    total_users = sum(engagement_dist.values())
    
    if total_users > 0:
        high_engagement_pct = (engagement_dist["high"] / total_users) * 100
        if high_engagement_pct > 30:
            insights.append(f"Excellent engagement: {high_engagement_pct:.1f}% of users are highly engaged")
        elif high_engagement_pct < 10:
            insights.append(f"Consider engagement initiatives: only {high_engagement_pct:.1f}% of users are highly engaged")
    
    # Usage insights
    avg_usage = weekly_analytics["avg_usage_per_user"]
    if avg_usage > 60:  # > 1 hour per week
        insights.append(f"Strong usage patterns: users average {avg_usage:.1f} minutes per week")
    elif avg_usage < 15:  # < 15 minutes per week
        insights.append(f"Low usage detected: users average only {avg_usage:.1f} minutes per week")
    
    return {
        "report_date": datetime.now(timezone.utc).isoformat(),
        "analytics": weekly_analytics,
        "key_insights": insights,
        "engagement_distribution": engagement_dist
    }
```

---

## Common Issues and Solutions

### Issue 1: Analytics Performance with Large Tenants
**Problem**: Slow analytics queries for tenants with many users
**Solution**: 
- Implement pagination for user processing
- Use aggregate queries instead of individual user calculations
- Cache frequently accessed analytics

### Issue 2: Inaccurate Engagement Calculations
**Problem**: Engagement levels don't reflect actual user behavior
**Solution**:
- Refine engagement algorithms based on real usage patterns
- Consider different metrics for different user types
- Implement A/B testing for engagement thresholds

### Issue 3: Memory Usage in Analytics
**Problem**: Loading too many users at once causes memory issues
**Solution**:
- Process users in batches
- Use streaming queries for large datasets
- Implement proper limits and pagination

---

## Verification Checklist

After completing this step, verify:

- [ ] Advanced analytics methods added to UserService
- [ ] User insights generation works with recommendations
- [ ] Tenant-level analytics provide comprehensive metrics
- [ ] Engagement level calculation is accurate
- [ ] Usage pattern analysis provides meaningful insights
- [ ] Performance optimizations implemented for large datasets
- [ ] Caching strategy considered for frequently accessed data
- [ ] Analytics methods handle edge cases gracefully

## Next Steps

Continue with **065b_User_Service_Testing_and_Integration.md** for:
- Comprehensive testing of analytics features
- FastAPI integration patterns
- Advanced testing scenarios
- Error handling validation
- Performance testing considerations

## Key Takeaways

1. **Advanced analytics** provide actionable insights for user engagement
2. **Engagement calculations** should be based on meaningful user behavior metrics
3. **Tenant-level analytics** enable organization-wide insights and decision-making
4. **Performance optimization** is crucial for analytics with large user bases
5. **Personalized recommendations** drive user engagement and feature adoption
6. **Caching strategies** improve performance for frequently accessed analytics
7. **Batch processing** handles large datasets efficiently
8. **Error handling** ensures analytics remain functional even with incomplete data
