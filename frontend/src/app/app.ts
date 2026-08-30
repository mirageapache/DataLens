import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Toast } from './shared/components/toast/toast';
import { Dialog } from './shared/components/dialog/dialog';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Toast, Dialog],
  templateUrl: './app.html'
})
export class App {
  protected readonly title = signal('frontend');
}
