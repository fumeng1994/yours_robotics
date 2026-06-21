import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, catchError, of, startWith } from 'rxjs';
import { RobotMasterModel } from './RobotMasterModel';

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

    // Turned into an observable stream that drops a null value while fetching
    robots$!: Observable<RobotMasterModel[] | null>;
    errorMessage: string = '';

    ngOnInit(): void {
        this.robots$ = this.http.get<RobotMasterModel[]>('http://localhost:5000/api/robots').pipe(
            catchError((error) => {
                console.error('Error fetching data:', error);
                this.errorMessage = 'Failed to load robot data. Is the API running?';
                return of([]); // Return empty array on crash to let the stream resolve safely
            }),
            startWith(null) // Directly pushes null first to show the loading placeholder
        );
    }

    goToRobot(robotId: string): void {
        this.router.navigate([`/${robotId}`]);
    }
}