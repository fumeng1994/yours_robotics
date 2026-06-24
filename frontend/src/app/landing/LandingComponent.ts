import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, startWith } from 'rxjs';
import { RobotMasterModel } from './RobotMasterModel';

export interface ZoneGroup {
    zoneName: string;
    robots: RobotMasterModel[];
    totalRevenue: number;
    totalInteractions: number;
    totalConvertedScans: number;
    totalScans: number;
}

@Component({
    selector: 'app-landing',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './LandingComponent.html',
    styleUrls: ['./LandingComponent.scss']
})
export class LandingComponent implements OnInit {
    private http = inject(HttpClient);
    private router = inject(Router);

    // Observable stream that emits grouped zones
    zoneGroups$!: Observable<ZoneGroup[] | null>;
    errorMessage: string = '';

    ngOnInit(): void {
        this.zoneGroups$ = this.http.get<RobotMasterModel[]>('http://localhost:5000/api/robots').pipe(
            map(robots => this.groupRobotsByZone(robots)),
            catchError((error) => {
                console.error('Error fetching data:', error);
                this.errorMessage = 'Failed to load robot data. Is the API running?';
                return of([]); // Return empty array on crash
            }),
            startWith(null)
        );
    }

    private groupRobotsByZone(robots: RobotMasterModel[]): ZoneGroup[] {
        const groups: { [key: string]: ZoneGroup } = {};

        for (const robot of robots) {
            if (!groups[robot.home_zone]) {
                groups[robot.home_zone] = {
                    zoneName: robot.home_zone,
                    robots: [],
                    totalRevenue: 0,
                    totalInteractions: 0,
                    totalConvertedScans: 0,
                    totalScans: 0
                };
            }
            groups[robot.home_zone].robots.push(robot);
            groups[robot.home_zone].totalRevenue += robot.total_revenue;
            groups[robot.home_zone].totalInteractions += robot.total_interactions;
            groups[robot.home_zone].totalConvertedScans += robot.converted_scans;
            groups[robot.home_zone].totalScans += robot.total_scans;
        }

        // Return an array sorted alphabetically by zone name (e.g., PDD-A, PDD-B...)
        return Object.values(groups).sort((a, b) => a.zoneName.localeCompare(b.zoneName));
    }

    goToRobot(robotId: string): void {
        this.router.navigate([`/${robotId}`]);
    }
}