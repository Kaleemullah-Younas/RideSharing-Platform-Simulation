import dash
from dash import dcc, html, Input, Output, callback_context
import plotly.graph_objs as go
import threading, time, random
import psutil
from scheduler import Scheduler, TaskType

app = dash.Dash(__name__)
scheduler = Scheduler()

# Create 20 riders
for i in range(1, 21):
    scheduler.add_rider(f"rider_{i}")

# Global thread handles
simulation_thread = None
trip_matching_thread = None
payment_thread = None
feedback_thread = None

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Ride-Sharing Platform Simulation", style={'textAlign': 'center', 'color': '#2c3e50'})
    ], style={'padding': '10px', 'backgroundColor': '#ecf0f1'}),

    # Control Buttons
    html.Div([
        html.Button('▶ Start', id='start-btn', n_clicks=0,
                    style={'outline': 'none',
                        'cursor': 'pointer',
                        'border': 'none',
                        'padding': '0.9rem 2rem',
                        'margin': '0',
                        'fontFamily': 'inherit',
                        'fontSize': '17px',
                        'position': 'relative',
                        'display': 'inline-block',
                        'letterSpacing': '0.05rem',
                        'fontWeight': '700',
                        'borderRadius': '500px',
                        'overflow': 'hidden',
                        'background': '#078c07',  # Green
                        'color': 'ghostwhite',
                        'transition': 'color 0.4s',
                        }),

        html.Button('⏹ Stop', id='stop-btn', n_clicks=0,
                    style={'outline': 'none',
                        'cursor': 'pointer',
                        'border': 'none',
                        'padding': '0.9rem 2rem',
                        'marginLeft': '10px',
                        'fontFamily': 'inherit',
                        'fontSize': '17px',
                        'position': 'relative',
                        'display': 'inline-block',
                        'letterSpacing': '0.05rem',
                        'fontWeight': '700',
                        'borderRadius': '500px',
                        'overflow': 'hidden',
                        'background': '#a10808',  # Red
                        'color': 'ghostwhite',
                        'transition': 'color 0.4s',
                        }),

        html.Button('⏻ Reset', id='reset-btn', n_clicks=0,
                    style={'outline': 'none',
                        'cursor': 'pointer',
                        'border': 'none',
                        'padding': '0.9rem 2rem',
                        'marginLeft': '10px',
                        'fontFamily': 'inherit',
                        'fontSize': '17px',
                        'position': 'relative',
                        'display': 'inline-block',
                        'letterSpacing': '0.05rem',
                        'fontWeight': '700',
                        'borderRadius': '500px',
                        'overflow': 'hidden',
                        'background': '#c27906',  # Orange (Reset)
                        'color': 'ghostwhite',
                        'transition': 'color 0.4s',
                        }),

        dcc.Interval(id='interval', interval=1000)
    ], style={'textAlign': 'center', 'marginTop': '10px'}),



    
    # Top Metrics: Trip Matched || Total Trips Completed || CPU Utilization
    html.Div([
        html.Div([
            html.H3("🏍️ Trip Matched", style={'marginBottom': '5px', 'color': '#27ae60'}),
            html.P(id='throughput', 
                style={'fontSize': '36px', 'color': '#27ae60', 
                        'fontWeight': 'bold', 'textAlign': 'center'})
        ], style={'width': '300px', 'padding': '20px', 'textAlign': 'center', 
                'borderRadius': '12px', 'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecfdf5'}),

            html.Div([
            html.H3("✅ Total Trips Completed", style={'marginBottom': '5px', 'color': '#2980b9'}),
            html.P(id='total-trips', 
                style={'fontSize': '36px', 'color': '#2980b9', 
                        'fontWeight': 'bold', 'textAlign': 'center'})
        ], style={'width': '300px', 'padding': '20px', 'textAlign': 'center', 
                'borderRadius': '12px', 'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ebf5ff'}),

        html.Div([
            html.H3("🖥️ CPU Utilization", style={'marginBottom': '5px', 'color': '#8e44ad'}),
            html.P(id='cpu-util', 
                style={'fontSize': '36px', 'color': '#8e44ad', 
                        'fontWeight': 'bold', 'textAlign': 'center'})
        ], style={'width': '300px', 'padding': '20px', 'textAlign': 'center', 
                'borderRadius': '12px', 'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#f5ebff'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '30px', 
            'marginTop': '20px', 'paddingBottom': '20px'}),

    
    # Row: Task Queue Size || Rider Status Grid
    html.Div([
        html.Div([
            html.H3("🧮 Task Queue Status", style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='task-queues', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'}),
        
        html.Div([
            html.H3("⌛ Rider Status Grid", style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='rider-status', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '2%', 
            'marginTop': '20px', 'paddingBottom': '20px'}),

    
    # Row: Trip Matching Response Time || Rider Details Visualization
    html.Div([
        html.Div([
            html.H3("🕝 Trip Matching Response Time", 
                    style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='response-times', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'}),
        
        html.Div([
            html.H3("🛣️ Rider Details", 
                    style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='rider-details', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '2%', 
            'marginTop': '20px', 'paddingBottom': '20px'}),

    
    # Row: Customer Feedback Distribution || Rider Ranking
    html.Div([
        html.Div([
            html.H3("📝 Customer Feedback", 
                    style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='customer-feedback', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'}),
        
        html.Div([
            html.H3("🏆 Rider Feedback Ranking", 
                    style={'textAlign': 'center', 'marginBottom': '10px', 'color': '#2c3e50'}),
            dcc.Graph(id='rider-ranking', style={'height': '350px'})
        ], style={'width': '48%', 'padding': '15px', 'borderRadius': '12px', 
                'boxShadow': '0px 4px 10px rgba(0, 0, 0, 0.1)', 
                'backgroundColor': '#ecf0f1', 'textAlign': 'center'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '2%', 
            'marginTop': '20px', 'paddingBottom': '20px'}),

    
    # Logs
    html.Div([
        html.H3("Logs", style={
            'textAlign': 'center',
            'color': '#34495e',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '24px',
            'marginBottom': '15px'
        }),
        html.Pre(id='log-display', style={
            'height': '300px',
            'overflowY': 'scroll',
            'background': '#ecf0f1',
            'color': '#2c3e50',
            'padding': '15px',
            'border': '1px solid #bdc3c7',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'fontFamily': 'Courier New, monospace',
            'fontSize': '14px',
            'lineHeight': '1.6',
            'whiteSpace': 'pre-wrap',  # To ensure long lines wrap
            'wordBreak': 'break-word'  # To prevent words from breaking awkwardly
        })
    ], style={
        'marginTop': '30px',
        'padding': '20px',
        'borderRadius': '10px',
        'backgroundColor': '#ffffff',
        'boxShadow': '0 6px 12px rgba(0, 0, 0, 0.1)',
        'maxWidth': '800px',
        'marginLeft': 'auto',
        'marginRight': 'auto'
    })
])

@app.callback(
    [Output('task-queues', 'figure'),
     Output('response-times', 'figure'),
     Output('rider-status', 'figure'),
     Output('customer-feedback', 'figure'),
     Output('rider-ranking', 'figure'),
     Output('rider-details', 'figure'),
     Output('throughput', 'children'),
     Output('total-trips', 'children'),
     Output('cpu-util', 'children'),
     Output('log-display', 'children')],
    [Input('interval', 'n_intervals'),
     Input('reset-btn', 'n_clicks')]
)
def update_gui(n_intervals, reset_clicks):
    ctx = callback_context
    triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''

    if "reset-btn" in triggered:
        scheduler.running = False
        scheduler.reset()

        # Reset Figures
        queue_fig = go.Figure(
            data=[go.Bar(x=['Trip Matching', 'Payment', 'Feedback'], y=[0, 0, 0],
                        marker_color=['#e74c3c', '#f1c40f', '#2ecc71'])],
            layout=go.Layout(
                plot_bgcolor='white',
                barmode='group',  # Group the bars together
                xaxis=dict(
                    title='Task Type',
                    tickmode='array',
                    tickvals=[0, 1, 2],
                    ticktext=['Trip Matching', 'Payment', 'Feedback'],
                    showgrid=True,  # Show grid
                ),
                yaxis=dict(
                    title='Queue Size',
                    range=[0, None],  # Ensure proper scaling
                    showgrid=True  # Show grid lines for y-axis
                ),
                shapes=[  # Add vertical grid lines
                    dict(
                        type='line',
                        line=dict(color='gray', width=2, dash='dot')
                    )
                ],
                margin=dict(l=50, r=50, t=50, b=50),  # Add margin for space
            )
        )
        
        resp_fig = go.Figure(
            data=[go.Scatter(
                y=[rt * 1000 for rt in scheduler.metrics['trip_response_times']], 
                mode='lines+markers', 
                line=dict(color='#027f9e', width=2, dash='solid'),
                marker=dict(size=6, color='grey', line=dict(width=0.5, color='black'))
            )],
            layout=go.Layout(
                xaxis=dict(
                    title='Time Interval',
                    range=[0, None],
                    showgrid=True,  # Enable grid lines
                    gridcolor='lightgray',  # Color for the grid lines
                    tickmode='auto',  # Automatically adjust tick marks
                    ticks='outside',  # Show ticks outside the plot
                    #ticklen=6,  # Length of the ticks
                    showline=True,  # Show axis line
                    linecolor='black',  # Axis line color
                ),
                yaxis=dict(
                    title='Response Time (ms)',
                    range=[0, None],
                    showgrid=True,  # Enable grid lines
                    gridcolor='lightgray',  # Color for the grid lines
                    #dtick=10,  # Set grid step to 100ms
                    ticks='outside',  # Show ticks outside the plot
                    #ticklen=6,  # Length of the ticks
                    showline=True,  # Show axis line
                    linecolor='black',  # Axis line color
                ),
                margin=dict(l=50, r=50, t=50, b=50),  # Add margin for space
                plot_bgcolor='white',
            )
        )
        rider_fig = go.Figure(
            data=[go.Bar(x=list(scheduler.riders.keys()), y=[1]*len(scheduler.riders),
                         marker_color=['gray']*len(scheduler.riders))],
            layout=go.Layout(
                xaxis=dict(type='category', title='Rider IDs'),
                yaxis=dict(visible=False, showticklabels=False),
                plot_bgcolor='white',
                margin=dict(l=50, r=50, t=50, b=50)
            )
        )
        
        feedback_fig = go.Figure(layout=go.Layout(plot_bgcolor='white'))
        ranking_fig = go.Figure(layout=go.Layout(plot_bgcolor='white'))
        details_fig = go.Figure(layout=go.Layout(plot_bgcolor='white'))
        return (queue_fig, resp_fig, rider_fig, feedback_fig, ranking_fig, details_fig,
                "0", "0", "0.0%", "Simulation reset.")

    # Task Queue Sizes (Bar Chart)
    queue_data = {
        'Trip Matching': scheduler.queues[TaskType.TRIP_MATCHING].qsize(),
        'Payment': scheduler.queues[TaskType.PAYMENT].qsize(),
        'Feedback': scheduler.queues[TaskType.FEEDBACK].qsize()
    }
    queue_fig = go.Figure(
        data=[go.Bar(x=list(queue_data.keys()), y=list(queue_data.values()),
                    marker_color=['#e74c3c', '#f1c40f', '#2ecc71'])],
        layout=go.Layout(
            plot_bgcolor='white',
            barmode='group',  # Group the bars together
            xaxis=dict(
                title='Task Type',
                tickmode='array',
                tickvals=[0, 1, 2],
                ticktext=['Trip Matching', 'Payment', 'Feedback'],
                showgrid=True,  # Show grid
            ),
            yaxis=dict(
                title='Queue Size',
                range=[0, max(queue_data.values()) + 1],  # Ensure proper scaling
                showgrid=True  # Show grid lines for y-axis
            ),
            shapes=[  # Add vertical grid lines
                dict(
                    type='line',
                    x0=i, x1=i,
                    y0=0, y1=max(queue_data.values()) + 1,
                    line=dict(color='gray', width=2, dash='dot')
                ) for i in range(len(queue_data))
            ],
            margin=dict(l=50, r=50, t=50, b=50),  # Add margin for space
        )
    )

    # Trip Matching Response Times (Line Plot)
    resp_fig = go.Figure(
        data=[go.Scatter(
            y=[rt * 1000 for rt in scheduler.metrics['trip_response_times']], 
            mode='lines+markers', 
            line=dict(color='#027f9e', width=2, dash='solid'),
            marker=dict(size=6, color='grey', line=dict(width=0.5, color='black'))
        )],
        layout=go.Layout(
            xaxis=dict(
                title='Time Interval',
                range=[0, None],
                showgrid=True,  # Enable grid lines
                gridcolor='lightgray',  # Color for the grid lines
                tickmode='auto',  # Automatically adjust tick marks
                ticks='outside',  # Show ticks outside the plot
                #ticklen=6,  # Length of the ticks
                showline=True,  # Show axis line
                linecolor='black',  # Axis line color
            ),
            yaxis=dict(
                title='Response Time (ms)',
                range=[0, None],
                showgrid=True,  # Enable grid lines
                gridcolor='lightgray',  # Color for the grid lines
                #dtick=10,  # Set grid step to 100ms
                ticks='outside',  # Show ticks outside the plot
                #ticklen=6,  # Length of the ticks
                showline=True,  # Show axis line
                linecolor='black',  # Axis line color
            ),
            #hovermode='closest',  # Make hover display closest point
            margin=dict(l=50, r=50, t=50, b=50),  # Add margin for space
            #title_x=0.5,  # Center the title
            #title_y=0.5,  # Place the title at the top
            plot_bgcolor='white',
            #showlegend=False  # Disable legend as it's not needed
        )
    )


    # Rider Status Grid (Colored Bar Chart)
    rider_ids = list(scheduler.riders.keys())
    rect_values = [1] * len(rider_ids)
    colors = []
    for rider in scheduler.riders.values():
        colors.append("gray" if rider['status'] == 'available' else "green")
    if not any(rider['status'] == 'available' for rider in scheduler.riders.values()):
        colors = ["red"] * len(colors)
    rider_fig = go.Figure(
        data=[go.Bar(x=rider_ids, y=rect_values, marker_color=colors)],
        layout=go.Layout(
            xaxis=dict(type='category', title='Rider IDs'),
            yaxis=dict(visible=False, showticklabels=False),
            plot_bgcolor='white',
            margin=dict(l=50, r=50, t=50, b=50)
        )
    )

    # Customer Feedback Distribution (Bar Chart)
    feedback_counts = [sum(1 for r in scheduler.riders.values() for f in r['feedback'] if f == i) 
                       for i in range(1, 6)]
    feedback_fig = go.Figure(
        data=[go.Bar(
            x=['⭐', '⭐⭐', '⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐⭐⭐'],
            y=feedback_counts,
            marker=dict(
                color=feedback_counts,  # Color by the count
                colorscale='Viridis',  # Gradient color scale
                showscale=False  # Display color scale
            )
        )],
        layout=go.Layout(
            plot_bgcolor='white',
            xaxis=dict(title='Feedback Rating'),
            yaxis=dict(title='Number of Feedbacks'),
            
            margin=dict(l=50, r=50, t=50, b=50)
        )
    )

    # Rider Ranking (Bar Chart with Ratings)
    rider_avg = [(rid, (sum(r['feedback']) / len(r['feedback'])) if r['feedback'] else 0) 
                 for rid, r in scheduler.riders.items()]
    rider_avg.sort(key=lambda x: x[1], reverse=True)
    ranking_fig = go.Figure(
        data=[go.Bar(
            x=[rid for rid, _ in rider_avg],
            y=[avg for _, avg in rider_avg],
            marker=dict(
                color=[avg for _, avg in rider_avg],  # Color based on rating
                colorscale="Blues",  # Gradient color effect
                #showscale=True  # Show color scale
            ),
            hoverinfo='x+y',
            text=[f"{avg:.1f}" for _, avg in rider_avg],  # Show values on bars
            textposition="auto",
            opacity=0.85  # Slight transparency for aesthetics
        )],
        layout=go.Layout(
            plot_bgcolor='white',
            xaxis=dict(
                title='Rider IDs',
                tickmode="linear",
                showgrid=True,
            ),
            yaxis=dict(
                title='Average Feedback',
                gridcolor="lightgray",
                range=[0, None]
            ),
            margin=dict(l=50, r=50, t=50, b=50)
        )
    )

    # Rider Details Visualization (Scatter Plot with Marker Size)
    xs, ys, sizes, avg_feedbacks, hover_texts = [], [], [], [], []
    for rid, rider in scheduler.riders.items():
        loc = rider["location"]
        xs.append(loc[0])
        ys.append(loc[1])
        sizes.append(10 + rider["trips_completed"] * 2)  # Adjusting size dynamically
        avg_fb = sum(rider["feedback"]) / len(rider["feedback"]) if rider["feedback"] else 0
        avg_feedbacks.append(avg_fb)
        
        # Hover details
        hover_texts.append(
            f"🆔 Rider: {rid}<br>🚕 Trips: {rider['trips_completed']}<br>⭐ Avg Feedback: {avg_fb:.1f}"
        )
    details_fig = go.Figure(
        data=[
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(
                    size=sizes,
                    color=avg_feedbacks,
                    colorscale="Plasma",  # More visually appealing color gradient
                    colorbar={"title": "Avg Feedback"},
                    line=dict(width=1, color="black"),
                    opacity=0.85,  # Slight transparency for a polished look
                ),
                hoverinfo="text",
                text=hover_texts,  # Show details only on hover
            )
        ],
        layout=go.Layout(
            xaxis=dict(title="X Location", showgrid=False, zeroline=False),
            yaxis=dict(title="Y Location", showgrid=False, zeroline=False),
            plot_bgcolor="white",
            paper_bgcolor="#f7f9fc",  # Soft background for a clean look
            margin=dict(l=40, r=40, t=20, b=40),
        ),
    )

    # CPU Utilization (Percentage Display)
    cpu_util_display = f"{psutil.cpu_percent(interval=0.1):.1f}%" if scheduler.running else "0.0%"

    # Logs Display (Text Display)
    logs_display = "\n".join(scheduler.logs[-100:])  # Show last 100 messages

    return (queue_fig, resp_fig, rider_fig, feedback_fig, ranking_fig, details_fig,
            str(scheduler.metrics['throughput']),
            str(scheduler.metrics['completed_trips']),
            cpu_util_display,
            logs_display)

@app.callback(
    [Output('start-btn', 'disabled'),
     Output('stop-btn', 'disabled')],
    [Input('start-btn', 'n_clicks'),
     Input('stop-btn', 'n_clicks')]
)
def control_simulation(start_clicks, stop_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return False, True
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    global simulation_thread, trip_matching_thread, payment_thread, feedback_thread
    if button_id == 'start-btn':
        if not scheduler.running:
            scheduler.reset()
            scheduler.running = True
            # Start threads for simulation
            trip_matching_thread = threading.Thread(target=scheduler.process_trip_matching_tasks)
            payment_thread = threading.Thread(target=scheduler.process_payment_tasks)
            feedback_thread = threading.Thread(target=scheduler.process_feedback_tasks)
            simulation_thread = threading.Thread(target=scheduler.simulate_task_arrivals)
            trip_matching_thread.start()
            payment_thread.start()
            feedback_thread.start()
            simulation_thread.start()
        return True, False
    elif button_id == 'stop-btn':
        scheduler.running = False
        return False, True
    return False, True

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)