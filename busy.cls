class Symbol is begin
	constructor() is skip;
end;


class Cell is begin
	var left_neighbour;
	var right_neighbour;
	var content;
	var default;
	
	constructor(default_content) is begin
		left_neighbour := self;
		right_neighbour := self;
		content := default_content;
		default := default_content
	end;
	
	method left() is begin
		if left_neighbour = self then
			begin
				left_neighbour := new Cell(default);
				left_neighbour.set_right(self)
			end
		else
			skip;
		
		return left_neighbour
	end;
	
	method set_left(l) is left_neighbour := l;
	
	method right() is begin
		if right_neighbour = self then
			begin
				right_neighbour := new Cell(default);
				right_neighbour.set_left(self)
			end
		else
			skip;
		
		return right_neighbour
	end;
	
	method set_right(r) is right_neighbour := r;
	
	method read() is return content;
	
	method write(c) is content := c;
end;


class TuringMachineB is begin
	var state_A; var state_B; var state_C;
	var char_0; var char_1;

	var head;
	var current_state;
	var true;
	var false;
	
	constructor() is begin
		state_A := new Symbol();
		state_B := new Symbol();
		state_C := new Symbol();
		char_0 := new Symbol();
		char_1 := new Symbol();
		
		head := new Cell(char_0);
		current_state := state_A;
		
		true := new Symbol();
		false := new Symbol();

		self.run()
	end;
	
	method run() is begin
		var stop;
		stop := false;
		
		while stop = false do
			stop := self.step()
	end;
	
	method step() is begin
		var c;
		
		c := head.read();
		
		if current_state = state_A then begin
			if c = char_0 then begin
				head.write(char_1);
				head := head.right();
				current_state := state_B;
				return false
			end
			else skip;
			
			if c = char_1 then begin
				head.write(char_1);
				head := head.left();
				current_state := state_C;
				return false
			end
			else skip
		end
		else skip;
		
		if current_state = state_B then begin
			if c = char_0 then begin
				head.write(char_1);
				head := head.left();
				current_state := state_A;
				return false
			end
			else skip;
			
			if c = char_1 then begin
				head.write(char_1);
				head := head.right();
				current_state := state_B;
				return false
			end
			else skip
		end
		else skip;

		if current_state = state_C then begin
			if c = char_0 then begin
				head.write(char_1);
				head := head.left();
				current_state := state_B;
				return false
			end
			else skip;
			
			if c = char_1 then begin
				head.write(char_1);
				head := head.right();
				return true
			end
			else skip
		end
		else skip;

		return true
	end;
end;

new TuringMachineB()
