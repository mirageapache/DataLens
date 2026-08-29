import { Component, OnInit, inject } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { AnalysisBlockComponent } from '../analysis-block/analysis-block.component';

@Component({
  selector: 'app-analysis-results-page',
  standalone: true,
  imports: [CommonModule, RouterModule, AnalysisBlockComponent],
  templateUrl: './analysis-results-page.html'
})
export class AnalysisResultsPage implements OnInit {
  private route = inject(ActivatedRoute);
  public location = inject(Location);

  taskId!: number;

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.taskId = +id;
      }
    });
  }
}
