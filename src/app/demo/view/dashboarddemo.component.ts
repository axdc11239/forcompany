import { Component, OnInit } from '@angular/core';
import { CarService } from '../service/carservice';
import { Car } from '../domain/car';
import { MenuItem } from 'primeng/primeng';
import { EventService } from '../service/eventservice';

@Component({
    templateUrl: './dashboard.component.html'
})
export class DashboardDemoComponent implements OnInit {

    cars: Car[];

    cols: any[];

    selectedCar: Car;

    items: MenuItem[];

    chartData: any;

    chartOptions: any;

    fullCalendarOptions: any;

    events: any[];

    constructor(private carService: CarService, private eventService: EventService) {}

    ngOnInit() {
        this.carService.getCarsMedium().then(cars => this.cars = cars);

        this.cols = [
            { field: 'vin', header: 'Vin' },
            { field: 'year', header: 'Year' },
            { field: 'brand', header: 'Brand' },
            { field: 'color', header: 'Color' }
        ];

        this.items = [
            { label: 'Save', icon: 'pi pi-check' },
            { label: 'Update', icon: 'pi pi-refresh' },
            { label: 'Delete', icon: 'pi pi-trash' },
        ];

        this.chartData = {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
            datasets: [{
                label: 'Sales',
                data: [12, 19, 3, 5, 2, 3, 9],
                borderColor: [
                    '#0F97C7',
                ],
                borderWidth: 3,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 3
            }, {
                label: 'Income',
                data: [1, 2, 5, 3, 12, 7, 15],
                backgroundColor: [
                    'rgba(187,222,251,0.2)',
                ],
                borderColor: [
                    '#578697',
                ],
                borderWidth: 3,
                fill: true
            },
            {
                label: 'Expenses',
                data: [1,2,3],
                borderColor: [
                    '#1BA7AF',
                ],
                borderWidth: 3,
                fill: false,
                pointRadius: [1,2,3]
            },
            {
                label: 'New Users',
                data: [3, 7, 2, 17, 15, 13, 19],
                borderColor: [
                    '#E2841A',
                ],
                borderWidth: 3,
                fill: false
            }]
        };

        this.chartOptions = {
            responsive: true,
            hover: {
                mode: 'index'
            },
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Month'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Value'
                    }
                }]
            }
        };

        this.eventService.getEvents().then(events => { this.events = events; });

        this.fullCalendarOptions = {
            defaultDate: '2016-01-12',
            header: {
                left: 'prev,next',
                center: 'title',
                right: 'month,agendaWeek,agendaDay'
            },
            editable: true
        };
    }
}
