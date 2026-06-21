import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { Observable, BehaviorSubject, map, catchError, of, combineLatest } from 'rxjs';
import { ChartConfiguration, ChartOptions } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

interface RobotEvent {
    event_category: 'interaction' | 'vending' | string;
    robot_id: string;
    timestamp: string;
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

    // Store raw data to avoid re-fetching on zoom
    private rawEvents$ = new BehaviorSubject<RobotEvent[]>([]);

    // Manage the current "Zoom" time window
    private timeWindow$ = new BehaviorSubject<{ start: number, end: number }>({
        start: new Date('2026-06-01T00:00:00Z').getTime(),
        end: new Date('2026-06-14T23:59:59Z').getTime()
    });

    // Separate chart configs for our "2 Boxes"
    interactionConfig$!: Observable<ChartConfiguration['data']>;
    vendingConfig$!: Observable<ChartConfiguration['data']>;
    commonChartOptions!: ChartOptions;

    // Array to populate day zoom buttons
    availableDays: number[] = [];

    ngOnInit(): void {
        this.robotId = this.route.snapshot.paramMap.get('id') || 'R-01';
        this.setupCommonOptions();
        this.generateDayButtons();

        // Fetch data once
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

        // Reactively build charts when data OR time window changes
        const filteredData$ = combineLatest([this.rawEvents$, this.timeWindow$]).pipe(
            map(([events, window]) => {
                return events.filter(e => {
                    const time = new Date(e.timestamp).getTime();
                    return time >= window.start && time <= window.end;
                }).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
            })
        );

        this.interactionConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'interaction', '#9b59b6', 'circle', 12)));
        this.vendingConfig$ = filteredData$.pipe(map(events => this.buildChartData(events, 'vending', '#3498db', 'circle', 8)));
    }

    private buildChartData(events: RobotEvent[], category: string, color: string, style: string, size: number): ChartConfiguration['data'] {
        const categoryEvents = events.filter(e => e.event_category === category).map(e => ({
            x: new Date(e.timestamp).getTime(),
            y: 1 // Fixed Y value since it's in its own box now
        }));

        return {
            datasets: [{
                label: category.toUpperCase(),
                data: categoryEvents as any,
                pointStyle: style,
                backgroundColor: color,
                borderColor: color,
                pointRadius: size,
                pointHoverRadius: size + 4
            }]
        };
    }

    private setupCommonOptions() {
        this.commonChartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const date = new Date(context.parsed.x as number);
                            return ` ${date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    display: false, // Hide Y axis completely to look like a solid box track
                    min: 0,
                    max: 2
                },
                x: {
                    type: 'linear',
                    position: 'bottom',
                    display: true,
                    grid: { display: false }, // Remove vertical grid lines for cleaner look
                    ticks: {
                        callback: (value) => {
                            const date = new Date(value as number);
                            // If zooming into a single day, show hours. Otherwise show days.
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

    // Add this near your other properties (like availableDays)
    activeView: 'full' | number = 'full';

    // --- ZOOM CONTROLS ---
    zoomToFull() {
        this.activeView = 'full'; // Set active state
        this.timeWindow$.next({
            start: new Date('2026-06-01T00:00:00Z').getTime(),
            end: new Date('2026-06-14T23:59:59Z').getTime()
        });
        this.updateXAxisScale();
    }

    zoomToDay(dayStartEpoch: number) {
        this.activeView = dayStartEpoch; // Set active state to the specific day
        this.timeWindow$.next({
            start: dayStartEpoch,
            end: dayStartEpoch + 86399999
        });
        this.updateXAxisScale();
    }

    private updateXAxisScale() {
        if (this.commonChartOptions?.scales?.['x']) {
            this.commonChartOptions.scales['x'].min = this.timeWindow$.value.start;
            this.commonChartOptions.scales['x'].max = this.timeWindow$.value.end;
        }
    }
}