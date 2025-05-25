def calculate_progress(current_savings, savings_goal):
    return (current_savings / savings_goal) * 100 if savings_goal > 0 else 0

def calculate_distance_from_goal(current_savings, savings_goal):
    return savings_goal - current_savings

def happiness_meter(expected_savings, actual_savings):
    if actual_savings < expected_savings:
        return "😞 You strayed from your savings goal!"
    elif actual_savings == expected_savings:
        return "😊 Great job! You met your savings goal!"
    else:
        return "🎉 Awesome! You exceeded your savings goal!"