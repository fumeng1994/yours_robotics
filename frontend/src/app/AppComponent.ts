import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet], // Only import RouterOutlet
  templateUrl: './AppComponent.html'
})
export class AppComponent {}