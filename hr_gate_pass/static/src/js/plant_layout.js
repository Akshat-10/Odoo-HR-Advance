/* static/src/js/plant_layout.js */

import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

class PlantLayoutView extends Component {
    setup() {
        this.state = useState({
            plantLayout: [],
            loading: true,
            error: null
        });

        this.orm = useService("orm");
        this.plantLayoutRef = useRef("plantLayout");

        onWillStart(async () => {
            await this.loadPlantLayoutData();
        });

        onMounted(() => {
            this.renderPlantLayout();
        });
    }

    async loadPlantLayoutData() {
        try {
            this.state.loading = true;
            const result = await rpc('/gate_pass/dashboard_data');

            if (result.success) {
                this.state.plantLayout = result.plant_layout || [];
                this.state.error = null;
            } else {
                this.state.error = result.error || 'Failed to load plant layout data';
            }
        } catch (error) {
            this.state.error = error.message || 'Failed to load plant layout data';
        } finally {
            this.state.loading = false;
        }
    }

    async refreshLayout() {
        await this.loadPlantLayoutData();
        this.renderPlantLayout();
    }

    renderPlantLayout() {
        if (!this.plantLayoutRef.el || !this.state.plantLayout.length) {
            return;
        }

        const container = this.plantLayoutRef.el;
        container.innerHTML = '';

        // Create plant layout with better styling
        const plantContainer = document.createElement('div');
        plantContainer.className = 'plant-container';
        plantContainer.innerHTML = `
            <div class="plant-background">
                <div class="plant-grid">
                    <!-- Grid lines for better visualization -->
                </div>
            </div>
        `;

        this.state.plantLayout.forEach(location => {
            const locationDiv = document.createElement('div');
            locationDiv.className = 'plant-location';
            locationDiv.style.cssText = `
                position: absolute;
                left: ${location.x}%;
                top: ${location.y}%;
                transform: translate(-50%, -50%);
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: ${location.color};
                border: 3px solid #fff;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
                z-index: 10;
            `;

            locationDiv.textContent = location.employee_count;

            // Create tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'location-tooltip';
            tooltip.innerHTML = `
                <strong>${location.name}</strong><br>
                Employees: ${location.employee_count}
            `;
            tooltip.style.cssText = `
                position: absolute;
                bottom: 50px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.9);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 11px;
                white-space: nowrap;
                opacity: 0;
                pointer-events: none;
                transition: all 0.3s ease;
                z-index: 20;
            `;

            locationDiv.appendChild(tooltip);

            locationDiv.addEventListener('mouseenter', () => {
                locationDiv.style.transform = 'translate(-50%, -50%) scale(1.3)';
                locationDiv.style.zIndex = '15';
                tooltip.style.opacity = '1';
            });

            locationDiv.addEventListener('mouseleave', () => {
                locationDiv.style.transform = 'translate(-50%, -50%) scale(1)';
                locationDiv.style.zIndex = '10';
                tooltip.style.opacity = '0';
            });

            plantContainer.appendChild(locationDiv);
        });

        container.appendChild(plantContainer);

        // Add legend
        const legend = document.createElement('div');
        legend.className = 'plant-legend';
        legend.innerHTML = `
            <div class="legend-item">
                <span class="legend-color" style="background-color: #9E9E9E;"></span>
                <span>No Employees</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #4CAF50;"></span>
                <span>1-5 Employees</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #FF9800;"></span>
                <span>6-15 Employees</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #F44336;"></span>
                <span>15+ Employees</span>
            </div>
        `;
        container.appendChild(legend);
    }
}

PlantLayoutView.template = 'hr_gate_pass.PlantLayoutTemplate';

// Register the action
registry.category("actions").add("plant_layout_view", PlantLayoutView);

export default PlantLayoutView;