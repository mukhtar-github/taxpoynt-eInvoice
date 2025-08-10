/**
 * Role Switcher Component
 * =======================
 * 
 * Dynamic role switching interface for hybrid users who have access
 * to both System Integrator (SI) and Access Point Provider (APP) roles.
 * 
 * Features:
 * - Seamless role switching with context preservation
 * - Interface-specific navigation and tools
 * - Permission-aware UI elements
 * - Activity tracking across role switches
 * - Quick access to role-specific workflows
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Select, Badge, Space, Alert, Tooltip, Dropdown, Avatar } from 'antd';
import {
  UserSwitchOutlined,
  IntegrationOutlined,
  SendOutlined,
  DashboardOutlined,
  SwapOutlined,
  CrownOutlined,
  TeamOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationTriangleOutlined
} from '@ant-design/icons';

import type { HybridRole, HybridUserSession, RecentActivity } from '../../types';

interface RoleSwitcherProps {
  currentRole: HybridRole;
  availableRoles: HybridRole[];
  userSession: HybridUserSession;
  onRoleSwitch: (newRole: HybridRole, context?: any) => void;
  onInterfaceSwitch: (interfaceType: 'si' | 'app' | 'hybrid') => void;
  className?: string;
  compact?: boolean;
}

interface RoleDefinition {
  role: HybridRole;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  permissions: string[];
  interfaces: ('si' | 'app' | 'hybrid')[];
  badge?: {
    text: string;
    color: string;
  };
}

const ROLE_DEFINITIONS: RoleDefinition[] = [
  {
    role: 'si_user',
    label: 'System Integrator',
    description: 'Focus on ERP/CRM integrations and data processing',
    icon: <IntegrationOutlined />,
    color: '#722ed1',
    permissions: ['si_view', 'si_manage', 'integration_config'],
    interfaces: ['si'],
  },
  {
    role: 'app_user',
    label: 'Access Point Provider',
    description: 'Manage FIRS transmissions and compliance reporting',
    icon: <SendOutlined />,
    color: '#1890ff',
    permissions: ['app_view', 'app_manage', 'transmission_config', 'security_audit'],
    interfaces: ['app'],
  },
  {
    role: 'hybrid_user',
    label: 'Hybrid User',
    description: 'Full access to both SI and APP capabilities with cross-role workflows',
    icon: <SwapOutlined />,
    color: '#13c2c2',
    permissions: ['si_view', 'si_manage', 'app_view', 'app_manage', 'hybrid_workflows', 'cross_role_analytics'],
    interfaces: ['si', 'app', 'hybrid'],
    badge: {
      text: 'Premium',
      color: 'gold'
    }
  },
  {
    role: 'platform_admin',
    label: 'Platform Admin',
    description: 'Full administrative access to all platform features and user management',
    icon: <CrownOutlined />,
    color: '#fa541c',
    permissions: ['admin_all', 'user_management', 'system_config', 'platform_monitoring'],
    interfaces: ['si', 'app', 'hybrid'],
    badge: {
      text: 'Admin',
      color: 'red'
    }
  }
];

export const RoleSwitcher: React.FC<RoleSwitcherProps> = ({
  currentRole,
  availableRoles,
  userSession,
  onRoleSwitch,
  onInterfaceSwitch,
  className,
  compact = false
}) => {
  const [switching, setSwitching] = useState(false);
  const [showContext, setShowContext] = useState(false);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);

  const currentRoleDef = ROLE_DEFINITIONS.find(def => def.role === currentRole);
  const availableRoleDefs = ROLE_DEFINITIONS.filter(def => availableRoles.includes(def.role));

  useEffect(() => {
    // Mock recent activities
    setRecentActivities([
      {
        activity_id: '1',
        type: 'role_switch',
        description: 'Switched to SI User role',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        interface: 'si',
        resource_id: 'role_switch_001'
      },
      {
        activity_id: '2',
        type: 'workflow_execution',
        description: 'Executed end-to-end invoice workflow',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        interface: 'hybrid',
        resource_id: 'workflow_001'
      }
    ]);
  }, [currentRole]);

  const handleRoleSwitch = async (newRole: HybridRole) => {
    if (newRole === currentRole) return;

    try {
      setSwitching(true);
      
      // Preserve context during role switch
      const context = {
        previousRole: currentRole,
        preserveWorkspace: true,
        timestamp: new Date()
      };

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onRoleSwitch(newRole, context);
    } catch (error) {
      console.error('Role switch failed:', error);
    } finally {
      setSwitching(false);
    }
  };

  const handleInterfaceSwitch = (interfaceType: 'si' | 'app' | 'hybrid') => {
    // Check if current role has access to the interface
    if (currentRoleDef && !currentRoleDef.interfaces.includes(interfaceType)) {
      // Find a suitable role for this interface
      const suitableRole = availableRoleDefs.find(def => 
        def.interfaces.includes(interfaceType)
      );
      
      if (suitableRole) {
        handleRoleSwitch(suitableRole.role);
      }
    }
    
    onInterfaceSwitch(interfaceType);
  };

  const renderRoleCard = (roleDef: RoleDefinition) => (
    <Card
      key={roleDef.role}
      size="small"
      style={{ 
        marginBottom: 8,
        border: roleDef.role === currentRole ? `2px solid ${roleDef.color}` : '1px solid #d9d9d9'
      }}
      hoverable={roleDef.role !== currentRole}
      onClick={() => roleDef.role !== currentRole && handleRoleSwitch(roleDef.role)}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ color: roleDef.color, marginRight: 8, fontSize: 16 }}>
            {roleDef.icon}
          </span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 2 }}>
              <strong>{roleDef.label}</strong>
              {roleDef.badge && (
                <Badge 
                  color={roleDef.badge.color}
                  text={roleDef.badge.text}
                  style={{ marginLeft: 8 }}
                />
              )}
            </div>
            <div style={{ fontSize: 12, color: '#666' }}>
              {roleDef.description}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {roleDef.role === currentRole ? (
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
          ) : (
            <Button 
              type="link" 
              size="small"
              loading={switching}
              icon={<SwapOutlined />}
            >
              Switch
            </Button>
          )}
        </div>
      </div>

      {/* Interface Access Indicators */}
      <div style={{ marginTop: 8 }}>
        <Space size={4}>
          {roleDef.interfaces.map(iface => (
            <Badge
              key={iface}
              color={
                iface === 'si' ? '#722ed1' :
                iface === 'app' ? '#1890ff' :
                '#13c2c2'
              }
              text={iface.toUpperCase()}
              style={{ fontSize: 10 }}
            />
          ))}
        </Space>
      </div>
    </Card>
  );

  const quickSwitchMenuItems = availableRoleDefs
    .filter(def => def.role !== currentRole)
    .map(def => ({
      key: def.role,
      icon: def.icon,
      label: (
        <div>
          <span>{def.label}</span>
          {def.badge && (
            <Badge 
              color={def.badge.color}
              text={def.badge.text}
              style={{ marginLeft: 8 }}
            />
          )}
        </div>
      ),
      onClick: () => handleRoleSwitch(def.role)
    }));

  const interfaceMenuItems = currentRoleDef?.interfaces.map(iface => ({
    key: iface,
    icon: iface === 'si' ? <IntegrationOutlined /> : 
          iface === 'app' ? <SendOutlined /> : <DashboardOutlined />,
    label: `${iface.toUpperCase()} Interface`,
    onClick: () => handleInterfaceSwitch(iface)
  })) || [];

  if (compact) {
    return (
      <div className={`role-switcher-compact ${className || ''}`}>
        <Space>
          <Dropdown 
            menu={{ items: quickSwitchMenuItems }}
            placement="bottomLeft"
            trigger={['click']}
          >
            <Button 
              type="text"
              icon={currentRoleDef?.icon}
              loading={switching}
            >
              {currentRoleDef?.label}
              {currentRoleDef?.badge && (
                <Badge 
                  color={currentRoleDef.badge.color}
                  text={currentRoleDef.badge.text}
                  style={{ marginLeft: 4 }}
                />
              )}
            </Button>
          </Dropdown>

          <Dropdown
            menu={{ items: interfaceMenuItems }}
            placement="bottomLeft"
            trigger={['click']}
          >
            <Button 
              type="text"
              icon={<SwapOutlined />}
              size="small"
            >
              Switch Interface
            </Button>
          </Dropdown>
        </Space>
      </div>
    );
  }

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <UserSwitchOutlined style={{ marginRight: 8 }} />
          Role & Interface Manager
          <Tooltip title="Switch between different user roles and interface views">
            <Button 
              type="link" 
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setShowContext(!showContext)}
            />
          </Tooltip>
        </div>
      }
      className={`role-switcher ${className || ''}`}
      extra={
        <Badge 
          status="processing"
          text={`Session: ${Math.floor((Date.now() - userSession.session_started.getTime()) / 60000)}m`}
        />
      }
    >
      {/* Current Role Status */}
      <Alert
        type="info"
        message={`Current Role: ${currentRoleDef?.label}`}
        description={
          <div>
            <p style={{ margin: '4px 0' }}>{currentRoleDef?.description}</p>
            <Space size={4}>
              <span style={{ fontSize: 12, color: '#666' }}>Access:</span>
              {currentRoleDef?.interfaces.map(iface => (
                <Badge
                  key={iface}
                  color={
                    iface === 'si' ? '#722ed1' :
                    iface === 'app' ? '#1890ff' :
                    '#13c2c2'
                  }
                  text={iface.toUpperCase()}
                  style={{ fontSize: 10 }}
                />
              ))}
            </Space>
          </div>
        }
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* Role Selection */}
      <div style={{ marginBottom: 16 }}>
        <h4 style={{ marginBottom: 12 }}>Available Roles</h4>
        {availableRoleDefs.map(renderRoleCard)}
      </div>

      {/* Quick Interface Access */}
      {currentRoleDef?.interfaces && currentRoleDef.interfaces.length > 1 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ marginBottom: 12 }}>Quick Interface Access</h4>
          <Space wrap>
            {currentRoleDef.interfaces.map(iface => (
              <Button
                key={iface}
                icon={
                  iface === 'si' ? <IntegrationOutlined /> :
                  iface === 'app' ? <SendOutlined /> :
                  <DashboardOutlined />
                }
                onClick={() => handleInterfaceSwitch(iface)}
                type={userSession.context.current_interface === iface ? 'primary' : 'default'}
              >
                {iface.toUpperCase()}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* Context & Recent Activity */}
      {showContext && (
        <div>
          <h4 style={{ marginBottom: 12 }}>Session Context</h4>
          
          {userSession.role_switched_at && (
            <Alert
              type="success"
              message={`Role switched ${Math.floor((Date.now() - userSession.role_switched_at.getTime()) / 60000)} minutes ago`}
              showIcon
              style={{ marginBottom: 12 }}
              size="small"
            />
          )}

          <div style={{ marginBottom: 12 }}>
            <strong>Recent Activities:</strong>
            {recentActivities.length > 0 ? (
              <ul style={{ margin: '8px 0 0 0', paddingLeft: 16 }}>
                {recentActivities.slice(0, 3).map(activity => (
                  <li key={activity.activity_id} style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                    {activity.description} - {activity.timestamp.toLocaleTimeString()}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ fontSize: 12, color: '#999', margin: '8px 0 0 0' }}>
                No recent activities
              </p>
            )}
          </div>

          <div>
            <strong>Permissions:</strong>
            <div style={{ marginTop: 4 }}>
              <Space wrap size={4}>
                {currentRoleDef?.permissions.map(permission => (
                  <Badge
                    key={permission}
                    color="blue"
                    text={permission.replace('_', ' ')}
                    style={{ fontSize: 10 }}
                  />
                ))}
              </Space>
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {availableRoles.length === 1 && (
        <Alert
          type="warning"
          message="Limited Role Access"
          description="Contact your administrator to request access to additional roles and features."
          showIcon
          style={{ marginTop: 16 }}
          size="small"
        />
      )}
    </Card>
  );
};

export default RoleSwitcher;