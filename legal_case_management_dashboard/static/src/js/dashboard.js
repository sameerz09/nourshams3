/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc"; // Fixed import
import { _t } from "@web/core/l10n/translation";
const { Component, onWillStart, onMounted, useState } = owl;

export class LegalDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.case_state = useState({
            case_count: 0,
            invoice_count: 0,
            trials_count: 0,
            evidences_count: 0,
            lawyers_count: 0,
            clients_count: 0,
        });

        onWillStart(this.onWillStart.bind(this));
        onMounted(this.onMounted.bind(this));
    }

    async onWillStart() {
        await this.fetch_data();
        await this._onWithoutFilter();
    }

    async onMounted() {
        this.render_filter();
    }

    async render_filter() {
        try {
            const result = await jsonrpc("/selection/field/lawyer");
            if (result) {
                const lawyerSelect = document.getElementById("lawyer_wise");
                lawyerSelect.innerHTML = result.map(
                    (lawyer) => `<option value="${lawyer.id}">${lawyer.name}</option>`
                ).join("");
            }
        } catch (error) {
            console.error("Error fetching lawyer list:", error);
        }
    }

    async fetch_data() {
        try {
            const result = await jsonrpc("/case/dashboard", {});
            if (result) {
                this.CaseManagementDashboard = result;
                this.case_state.clients_count = result.clients_in_case;

                google.charts.load("current", { packages: ["corechart"] });
                google.charts.setOnLoadCallback(() => this.drawCharts(result));
            }
        } catch (error) {
            console.error("Error fetching case dashboard data:", error);
        }
    }

    drawCharts(result) {
        try {
            // Pie Chart
            const pieData = google.visualization.arrayToDataTable(result["case_category"]);
            new google.visualization.PieChart(document.getElementById("pie_chart"))
                .draw(pieData, { backgroundColor: "transparent", is3D: true });

            // Donut Chart
            const donutData = google.visualization.arrayToDataTable(result.top_10_cases);
            new google.visualization.PieChart(document.getElementById("donut_chart"))
                .draw(donutData, { backgroundColor: "transparent", pieHole: 0.5 });

            // Line Chart
            const lineData = google.visualization.arrayToDataTable(result["data_list"]);
            new google.visualization.LineChart(document.getElementById("mygraph"))
                .draw(lineData, { backgroundColor: "transparent", legend: "none" });

            // Column Chart
            const columnData = google.visualization.arrayToDataTable(result.stage_count);
            new google.visualization.ColumnChart(document.getElementById("column_graph"))
                .draw(columnData, { backgroundColor: "transparent", legend: "none" });
        } catch (e) {
            console.error("Error drawing charts:", e);
        }
    }

    async _onWithoutFilter() {
        try {
            const value = await jsonrpc("/dashboard/without/filter", {});
            if (value) {
                this.case_state.case_count = value.total_case || 0;
                this.case_state.invoice_count = value.total_invoiced || 0;
                this.case_state.trials_count = value.trials || 0;
                this.case_state.evidences_count = value.evidences || 0;
                this.case_state.lawyers_count = value.lawyers || 0;
                this.case_state.clients_count = value.clients || 0;
            }
        } catch (error) {
            console.error("Error in _onWithoutFilter:", error);
        }
    }

    async _onchangeStageFilter() {
        try {
            const data = {
                stage: document.getElementById("stage_wise").value,
                lawyer: document.getElementById("lawyer_wise").value,
                month_wise: document.getElementById("month_wise").value,
            };

            const value = await jsonrpc("/dashboard/filter", { data });
            if (value) {
                this.case_state.case_count = value.total_case.length || 0;
                this.case_state.invoice_count = value.total_invoiced || 0;
                this.case_state.trials_count = value.trials.length || 0;
                this.case_state.evidences_count = value.evidences.length || 0;
                this.case_state.lawyers_count = value.lawyers.length || 0;
                this.case_state.clients_count = value.clients.length || 0;
            }
        } catch (error) {
            console.error("Error in _onchangeStageFilter:", error);
        }
    }

    openActionWindow(name, model, list) {
        this.action.doAction({
            name: _t(name),
            type: "ir.actions.act_window",
            res_model: model,
            view_mode: "tree,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", list]],
            context: { create: false },
            target: "current",
        });
    }

    _OnClickTotalClients() {
        this.openActionWindow("Total Clients", "res.partner", this.case_state.clients_count);
    }

    _OnClickTotalTrials() {
        this.openActionWindow("Total Trials", "legal.trial", this.case_state.trials_count);
    }

    _OnClickTotalLawyers() {
        this.openActionWindow("Total Lawyers", "hr.employee", this.case_state.lawyers_count);
    }

    _OnClickTotalEvidences() {
        this.openActionWindow("Total Evidences", "legal.evidence", this.case_state.evidences_count);
    }

    _OnClickTotalCase() {
        this.openActionWindow("Total Cases", "case.registration", this.case_state.case_count);
    }
}

LegalDashboard.template = "CaseDashBoard";
registry.category("actions").add("case_dashboard_tags", LegalDashboard);
