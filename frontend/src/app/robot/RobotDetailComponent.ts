import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Observable, map, startWith, catchError, of } from 'rxjs'; // Added map, catchError, of
import { RobotDetailModel } from './RobotDetailModel';
import { RobotEventComponent } from './RobotEventComponent';

@Component({
    selector: 'app-robot',
    standalone: true,
    imports: [CommonModule, RouterModule, RobotEventComponent],
    templateUrl: './RobotDetailComponent.html',
    styleUrls: ['./RobotDetailComponent.scss']
})
export class RobotDetailComponent implements OnInit {
    private route = inject(ActivatedRoute);
    private http = inject(HttpClient);

    robotId: string | null = '';
    robotDetails$!: Observable<RobotDetailModel[] | null>; 
    errorMessage: string = '';

    ngOnInit(): void {
        this.robotId = this.route.snapshot.paramMap.get('id');

        if (this.robotId) {
            this.robotDetails$ = this.http.get(
                `http://localhost:5000/api/robot/${this.robotId}`,
                { responseType: 'text' } // 1. Read raw text response instead of auto-parsing JSON
            ).pipe(
                map((rawText: string) => {
                    // 2. Sanitize malicious/invalid NaN values into valid JSON nulls
                    const sanitizedText = rawText.replace(/:\s*NaN\b/g, ': null');
                    
                    // 3. Manually parse the clean text string
                    return JSON.parse(sanitizedText) as RobotDetailModel[];
                }),
                catchError((error) => {
                    console.error('Parsing error caught:', error);
                    this.errorMessage = `Could not process data logs for robot ${this.robotId} due to bad telemetry values.`;
                    return of([]); // Return an empty array so the stream completes safely
                }),
                startWith(null)
            );
        }
    }
}