import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { Observable, BehaviorSubject, map, combineLatest } from 'rxjs';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

interface ErrorAggregate {
    category: string;
    errorClass: string;
    errorColumn: string;
    count: number;
}

interface RobotEvent {
    event_category: 'interaction' | 'vending' | 'nav_event' | 'telemetry' | string;
    robot_id: string;
    timestamp: string;
    meta: Record<string, any>;
    error?: boolean;
    errorClass?: string;
    errorColumn?: string;
    anomally?: string;
}

@Component({
    selector: 'app-robot-event',
    standalone: true,
    imports: [CommonModule, BaseChartDirective],
    templateUrl: './RobotEventComponent.html',
    styleUrls: ['./RobotEventComponent.scss']
})
export class RobotEventComponent implements OnInit {
    private route = inject(ActivatedRoute);
    private http = inject(HttpClient);

    robotId: string | null = '';
    errorMessage: string = '';

    private rawEvents$ = new BehaviorSubject<RobotEvent[]>([]);
    private timeWindow$ = new BehaviorSubject<{ start: number, end: number }>({
        start: new Date('2026-06-01T00:00:00Z').getTime(),
        end: new Date('2026-06-14T23:59:59Z').getTime()
    });

    // 5 Tracks for configs
    errorConfig$!: Observable<ChartConfiguration['data']>;
    interactionConfig$!: Observable<ChartConfiguration['data']>;
    vendingConfig$!: Observable<ChartConfiguration['data']>;
    navConfig$!: Observable<ChartConfiguration['data']>;
    telemetryConfig$!: Observable<ChartConfiguration['data']>;

    commonChartOptions!: ChartOptions;
    availableDays: number[] = [];
    activeView: 'full' | number = 'full';
    errorSummary$!: Observable<RobotEvent[]>;
    topErrors$!: Observable<ErrorAggregate[]>;
    telemetryAnomalies$ = new BehaviorSubject<RobotEvent[]>([]);

    // 1. ADD FILTER & SORT STATE VARIABLES
    searchTerm$ = new BehaviorSubject<string>('');
    sortConfig$ = new BehaviorSubject<{ column: string, direction: 'asc' | 'desc' }>({
        column: 'timestamp',
        direction: 'desc'
    });

    // 2. ADD DISPLAY OBSERVABLE
    displayedErrors$!: Observable<RobotEvent[]>;

    selectedCategory$ = new BehaviorSubject<string>('interaction');
    eventSortConfig$ = new BehaviorSubject<{ column: string, direction: 'asc' | 'desc' }>({
        column: 'timestamp',
        direction: 'desc'
    });

    categorizedEvents$!: Observable<RobotEvent[]>;

    ngOnInit(): void {
        this.robotId = this.route.snapshot.paramMap.get('id') || 'R-10';
        this.setupCommonOptions();
        this.generateDayButtons();

        this.http.get(`http://localhost:5000/api/robot/${this.robotId}/event`, { responseType: 'text' })
            .subscribe({
                next: (rawText) => {
                    const sanitized = rawText.replace(/:\s*NaN\b/g, ': null');
                    this.rawEvents$.next(JSON.parse(sanitized));

                },
                error: (err) => {
                    console.error(err);
                    this.errorMessage = 'Failed to load timeline events.';
                }
            });

        this.http.get(`http://localhost:5000/api/robot/${this.robotId}/anomally`, { responseType: 'text' })
            .subscribe({
                next: (rawText) => {
                    const sanitized = rawText.replace(/:\s*NaN\b/g, ': null');
                    this.telemetryAnomalies$.next(JSON.parse(sanitized));
                },
                error: (err) => {
                    console.error('Failed to load anomalies:', err);
                }
            });

        const filteredData$ = combineLatest([this.rawEvents$, this.timeWindow$]).pipe(
            map(([events, window]) => {
                return events.filter(e => {
                    const time = new Date(e.timestamp).getTime();
                    return time >= window.start && time <= window.end;
                }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
            })
        );

        this.errorSummary$ = filteredData$.pipe(
            map(events => events.filter(e => e.error === true))
        );

        this.topErrors$ = this.errorSummary$.pipe(
            map(errors => {
                const counts = new Map<string, ErrorAggregate>();

                errors.forEach(err => {
                    const category = err.event_category || 'unknown';
                    const errorClass = err.errorClass || 'UNKNOWN';
                    const errorColumn = err.errorColumn || 'N/A';

                    // Create a unique composite key for grouping
                    const key = `${category}|${errorClass}|${errorColumn}`;

                    if (counts.has(key)) {
                        counts.get(key)!.count++;
                    } else {
                        counts.set(key, { category, errorClass, errorColumn, count: 1 });
                    }
                });

                // Convert map to array, sort descending by count, and slice top 3
                return Array.from(counts.values())
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 3);
            })
        );

        this.displayedErrors$ = combineLatest([
            this.errorSummary$,
            this.searchTerm$,
            this.sortConfig$
        ]).pipe(
            map(([errors, search, sort]) => {
                // Step 1: Filter
                let result = errors;
                if (search.trim()) {
                    const term = search.toLowerCase();
                    result = errors.filter(e =>
                        e.event_category?.toLowerCase().includes(term)
                        || e.errorClass?.toLowerCase().includes(term)
                        || e.errorColumn?.toLowerCase().includes(term)
                        // ||  this.getMetaSummary(e.meta).toLowerCase().includes(term)
                    );
                }

                // Step 2: Sort
                return result.sort((a, b) => {
                    let valA: any = a[sort.column as keyof RobotEvent];
                    let valB: any = b[sort.column as keyof RobotEvent];

                    // Handle special sorting cases
                    if (sort.column === 'meta') {
                        valA = this.getMetaSummary(a.meta);
                        valB = this.getMetaSummary(b.meta);
                    } else if (sort.column === 'timestamp') {
                        valA = new Date(a.timestamp).getTime();
                        valB = new Date(b.timestamp).getTime();
                    }

                    // Treat undefined/null as empty strings for safe sorting
                    valA = valA || '';
                    valB = valB || '';

                    if (valA < valB) return sort.direction === 'asc' ? -1 : 1;
                    if (valA > valB) return sort.direction === 'asc' ? 1 : -1;
                    return 0;
                });
            })
        );

        // Map configs across all tracks. The 'all_errors' virtual category captures any event flagged as an error.
        this.errorConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'all_errors', '#e74c3c', 'star', 12)));
        this.interactionConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'interaction', '#9b59b6', 'circle', 10)));
        this.vendingConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'vending', '#3498db', 'rect', 9)));
        this.navConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'nav_event', '#e67e22', 'triangle', 10)));
        this.telemetryConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'telemetry', '#2ecc71', 'rectRot', 8)));

        this.categorizedEvents$ = combineLatest([
            filteredData$, // Reuse your existing time-window filtered data
            this.selectedCategory$,
            this.eventSortConfig$
        ]).pipe(
            map(([events, category, sort]) => {
                // Filter by selected tab
                const filtered = events.filter(e => e.event_category === category);

                // Sort the results
                return filtered.sort((a, b) => {
                    let valA: any = a[sort.column as keyof RobotEvent];
                    let valB: any = b[sort.column as keyof RobotEvent];

                    if (sort.column === 'meta') {
                        valA = this.getMetaSummary(a.meta);
                        valB = this.getMetaSummary(b.meta);
                    } else if (sort.column === 'timestamp') {
                        valA = new Date(a.timestamp).getTime();
                        valB = new Date(b.timestamp).getTime();
                    }

                    valA = valA || '';
                    valB = valB || '';

                    if (valA < valB) return sort.direction === 'asc' ? -1 : 1;
                    if (valA > valB) return sort.direction === 'asc' ? 1 : -1;
                    return 0;
                });
            })
        );
    }

    private buildChartData(events: RobotEvent[], category: string, defaultColor: string, style: any, size: number): ChartConfiguration['data'] {
        // Filter down to the specific category, OR capture any global error
        const filteredEvents = category === 'all_errors'
            ? events.filter(e => e.error === true)
            : events.filter(e => e.event_category === category);

        // Build the data array, pulling up the new error API fields for tooltips
        const categoryData = filteredEvents.map(e => ({
            x: new Date(e.timestamp).getTime(),
            y: 1,
            meta: e.meta,
            errorClass: e.errorClass,
            errorColumn: e.errorColumn
        }));

        // Build array of colors using the new API error flag
        const errorColor = '#e74c3c';
        const backgroundColors = filteredEvents.map(e =>
            e.error === true ? errorColor : defaultColor
        );

        return {
            datasets: [{
                label: category === 'all_errors' ? 'ERRORS' : category.toUpperCase(),
                data: categoryData as any,
                pointStyle: style,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors,
                pointRadius: size,
                pointHoverRadius: size + 4
            }]
        };
    }

    private setupCommonOptions() {
        this.commonChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: { right: 30, left: 10 }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const date = new Date(context.parsed.x as number);
                            const timestampStr = date.toLocaleString('en-US', {
                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
                            });

                            const lines = [`Time: ${timestampStr}`];
                            const rawPoint = context.dataset.data[context.dataIndex] as any;

                            // Include the new API error context in the tooltip
                            if (rawPoint?.errorClass) lines.push(`Error Class: ${rawPoint.errorClass}`);
                            if (rawPoint?.errorColumn) lines.push(`Error Column: ${rawPoint.errorColumn}`);

                            if (rawPoint?.meta) {
                                Object.entries(rawPoint.meta).forEach(([key, val]) => {
                                    if (val !== null && val !== undefined && !Number.isNaN(val)) {
                                        lines.push(`${key}: ${val}`);
                                    }
                                });
                            }
                            return lines;
                        }
                    }
                }
            },
            scales: {
                y: { display: false, min: 0, max: 2 },
                x: {
                    type: 'linear',
                    position: 'bottom',
                    display: true,
                    grid: { display: true, color: '#e2e8f0' },
                    min: this.timeWindow$.value.start,
                    max: this.timeWindow$.value.end,
                    ticks: {
                        autoSkip: false,
                        stepSize: 86400000,
                        maxRotation: 45,
                        callback: (value) => {
                            const date = new Date(value as number);
                            const windowRange = this.timeWindow$.value.end - this.timeWindow$.value.start;
                            const isDayView = windowRange <= 86400000;
                            return isDayView
                                ? date.toLocaleTimeString('en-US', { hour: 'numeric' })
                                : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        }
                    }
                }
            }
        };
    }

    private generateDayButtons() {
        const start = new Date('2026-06-01T00:00:00Z').getTime();
        for (let i = 0; i < 14; i++) {
            this.availableDays.push(start + (i * 86400000));
        }
    }

    zoomToFull() {
        this.activeView = 'full';
        this.timeWindow$.next({
            start: new Date('2026-06-01T00:00:00Z').getTime(),
            end: new Date('2026-06-14T23:59:59Z').getTime()
        });
        this.updateXAxisScale();
    }

    zoomToDay(dayStartEpoch: number) {
        this.activeView = dayStartEpoch;
        this.timeWindow$.next({
            start: dayStartEpoch,
            end: dayStartEpoch + 86399999
        });
        this.updateXAxisScale();
    }

    private updateXAxisScale() {
        this.commonChartOptions = {
            ...this.commonChartOptions,
            scales: {
                ...this.commonChartOptions.scales,
                x: {
                    ...this.commonChartOptions.scales?.['x'],
                    min: this.timeWindow$.value.start,
                    max: this.timeWindow$.value.end
                }
            }
        };
    }

    private isErrorEvent(category: string, meta: any): boolean {
        if (!meta) return false;

        if (category === 'nav_event') {
            const errorTypes = ['fault', 'estop', 'manual_takeover'];
            const errorCodes = ['SYS-500', 'SAF-201', 'OPS-301', 'NAV-101'];
            return errorTypes.includes(meta.event_type) || errorCodes.includes(meta.code);
        }

        if (category === 'interaction') {
            const errorOutcomes = ['error', 'abandoned'];
            return errorOutcomes.includes(meta.outcome);
        }

        if (category === 'vending') {
            const errorStatuses = ['failed', 'refunded'];
            return errorStatuses.includes(meta.payment_status);
        }

        return false;
    }

    getMetaSummary(meta: any): string {
        if (!meta) return 'N/A';

        return Object.entries(meta)
            .filter(([key, val]) => val !== null && val !== undefined && !Number.isNaN(val) && key !== 'code' && key !== 'event_type')
            .map(([key, val]) => `${key}: ${val}`)
            .join(', ') || 'No additional details';
    }

    // 4. ADD UI ACTION METHODS
    onSearch(event: Event) {
        const input = event.target as HTMLInputElement;
        this.searchTerm$.next(input.value);
    }

    sortBy(column: string) {
        const current = this.sortConfig$.value;
        if (current.column === column) {
            // Toggle direction if clicking the same column
            this.sortConfig$.next({
                column,
                direction: current.direction === 'asc' ? 'desc' : 'asc'
            });
        } else {
            // Default to descending for timestamps, ascending for text
            const defaultDir = column === 'timestamp' ? 'desc' : 'asc';
            this.sortConfig$.next({ column, direction: defaultDir });
        }
    }

    getSortIcon(column: string): string {
        const config = this.sortConfig$.value;
        if (config.column !== column) return '↕';
        return config.direction === 'asc' ? '↑' : '↓';
    }

    // 3. ADD TAB & SORT METHODS
    selectEventCategory(category: string) {
        this.selectedCategory$.next(category);
    }

    sortEventList(column: string) {
        const current = this.eventSortConfig$.value;
        if (current.column === column) {
            this.eventSortConfig$.next({
                column,
                direction: current.direction === 'asc' ? 'desc' : 'asc'
            });
        } else {
            const defaultDir = column === 'timestamp' ? 'desc' : 'asc';
            this.eventSortConfig$.next({ column, direction: defaultDir });
        }
    }

    getEventSortIcon(column: string): string {
        const config = this.eventSortConfig$.value;
        if (config.column !== column) return '↕';
        return config.direction === 'asc' ? '↑' : '↓';
    }
}