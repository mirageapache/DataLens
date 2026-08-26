import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChartSwitcherComponent } from './chart-switcher.component';
import { By } from '@angular/platform-browser';

describe('ChartSwitcherComponent', () => {
  let component: ChartSwitcherComponent;
  let fixture: ComponentFixture<ChartSwitcherComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChartSwitcherComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ChartSwitcherComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render available charts', () => {
    component.availableCharts = ['bar', 'line', 'pie'];
    component.activeChart = 'bar';
    fixture.detectChanges();

    const buttons = fixture.debugElement.queryAll(By.css('button'));
    expect(buttons.length).toBe(3);
    
    // Check if the first button has the active class and correct icon
    const firstButton = buttons[0].nativeElement;
    expect(firstButton.classList).toContain('bg-white'); // The active class contains bg-white
    expect(firstButton.querySelector('i').classList).toContain('fa-chart-column');
    expect(firstButton.textContent.trim()).toBe('長條圖');
  });

  it('should ignore unknown chart types', () => {
    component.availableCharts = ['bar', 'unknown_chart'];
    fixture.detectChanges();

    const buttons = fixture.debugElement.queryAll(By.css('button'));
    expect(buttons.length).toBe(1);
    expect(buttons[0].nativeElement.textContent.trim()).toBe('長條圖');
  });

  it('should emit chartTypeChange event when selecting a different chart', () => {
    const emitSpy = vi.spyOn(component.chartTypeChange, 'emit');
    component.availableCharts = ['bar', 'line'];
    component.activeChart = 'bar';
    fixture.detectChanges();

    const buttons = fixture.debugElement.queryAll(By.css('button'));
    // Click on line chart (2nd button)
    buttons[1].triggerEventHandler('click', null);
    
    expect(component.activeChart).toBe('line');
    expect(emitSpy).toHaveBeenCalledWith('line');
  });

  it('should not emit chartTypeChange event when selecting the same chart', () => {
    const emitSpy = vi.spyOn(component.chartTypeChange, 'emit');
    component.availableCharts = ['bar', 'line'];
    component.activeChart = 'bar';
    fixture.detectChanges();

    const buttons = fixture.debugElement.queryAll(By.css('button'));
    // Click on bar chart (1st button) again
    buttons[0].triggerEventHandler('click', null);
    
    expect(emitSpy).not.toHaveBeenCalled();
  });
});
