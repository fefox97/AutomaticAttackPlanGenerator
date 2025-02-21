var icBgAnimation = function() {
	var width,
			height,
			largeHeader,
			canvas,
			ctx,
			points,
			target,
			animateHeader = true;
    var glyphcolor = [49, 49, 106];
    var linecolor = [70, 70, 106];
    var glyphcolordark = [246, 241, 0];
    var linecolordark = [255, 235, 0];
	initTop();
	initIcBgAnimation();
	addEventListeners();

	function initTop() {
		width = window.innerWidth;
		height = window.innerHeight;
		target = {
			x: width / 2,
			y: height / 2
		};

		canvas = document.getElementById("icbg-animation");
		canvas.width = width;
		canvas.height = height;
		ctx = canvas.getContext("2d");

		// create lines and points
		points = [];
		for (var x = 0; x < width; x = x + width / 18) {
			for (var y = 0; y < height; y = y + height / 15) {
				var px = x + Math.random() * width / 4;
				var py = y + Math.random() * height / 2;
				var p = {
					x: px,
					originX: px,
					y: py,
					originY: py
				};
				points.push(p);
			}
		}

		// for each point find the 5 closest points
		for (var i = 0; i < points.length; i++) {
			var closest = [];
			var p1 = points[i];
			for (var j = 0; j < points.length; j++) {
				var p2 = points[j];
				if (!(p1 == p2)) {
					var placed = false;
					for (var k = 0; k < 4; k++) {
						if (!placed) {
							if (closest[k] == undefined) {
								closest[k] = p2;
								placed = true;
							}
						}
					}
					for (var k = 0; k < 4; k++) {
						if (!placed) {
							if (getDistance(p1, p2) < getDistance(p1, closest[k])) {
								closest[k] = p2;
								placed = true;
							}
						}
					}
				}
			}
			p1.closest = closest;
		}

		// assign a circle to each point
		for (var i in points) {
			var c = new Circle(points[i], 2 + Math.random() * 6, glyphcolor);
			points[i].circle = c;
		}
	}

	// Mouse and touch event handling
	function addEventListeners() {
		if (!("ontouchstart" in window)) {
			window.addEventListener("mousemove", mouseMove);
		}
		window.addEventListener("scroll", scrollCheck);
		window.addEventListener("resize", resize);
	}

	function mouseMove(e) {
		var posx = (posy = 0);
		if (e.pageX || e.pageY) {
			posx =
				e.pageX - (document.body.scrollLeft + document.documentElement.scrollLeft);
			posy =
				e.pageY - (document.body.scrollTop + document.documentElement.scrollTop);
		} else if (e.clientX || e.clientY) {
			posx = e.clientX;
			posy = e.clientY;
		}
		target.x = posx;
		target.y = posy;
	}

	function scrollCheck() {
		if (jQuery(document).scrollTop() > height / 2) animateHeader = true;
		else animateHeader = false;
	}

	function resize() {
		width = window.innerWidth;
		height = window.innerHeight;
		canvas.width = width;
		canvas.height = height;
	}

	// animation
	function initIcBgAnimation() {
		animate();
		for (var i in points) {
			shiftPoint(points[i]);
		}
	}

	function animate() {
		// color settings for lines below
		if (animateHeader) {
			ctx.clearRect(0, 0, width, height);

			for (var i in points) {
				// detect points in range
				if (Math.abs(getDistance(target, points[i])) < 4000) {
					points[i].active = 0.09;
					points[i].circle.active = 0.13;
				} else if (Math.abs(getDistance(target, points[i])) < 20000) {
					points[i].active = 0.08;
					points[i].circle.active = 0.12;
				} else if (Math.abs(getDistance(target, points[i])) < 40000) {
					points[i].active = 0.05;
					points[i].circle.active = 0.10;
				} else {
					points[i].active = 0.03;
					points[i].circle.active = 0.05;
				}

				drawLines(points[i]);
				points[i].circle.draw();
			}
		}
		requestAnimationFrame(animate);
	}
	// speed of movement adjusted below
	function shiftPoint(p) {
		TweenLite.to(p, 40 + 15 * Math.random(), {
			x: p.originX - 50 + Math.random() * 200,
			y: p.originY - 50 + Math.random() * 150,
			ease: Circ.easeInOut,
			onComplete: function() {
				shiftPoint(p);
			}
		});
	}

	// Canvas manipulation
	function drawLines(p) {
		if (!p.active) return;
		for (var i in p.closest) {
			ctx.beginPath();
			ctx.moveTo(p.x, p.y);
			ctx.lineTo(p.closest[i].x, p.closest[i].y);
            if (document.documentElement.getAttribute('data-bs-theme') == 'dark') {
                ctx.strokeStyle = "rgba("+linecolordark[0]+","+linecolordark[1]+","+linecolordark[2]+"," + p.active + ")";
            }
            else {
			    ctx.strokeStyle = "rgba("+linecolor[0]+","+linecolor[1]+","+linecolor[2]+"," + p.active + ")";
            }
			ctx.stroke();
		}
	}

	function Circle(pos, rad, color) {
		var _this = this;

		// constructor
		(function() {
			_this.pos = pos || null;
			_this.radius = rad || null;
			_this.color = color || null;
		})();

		this.draw = function() {
			if (!_this.active) return;
			ctx.beginPath();
			ctx.arc(_this.pos.x, _this.pos.y, _this.radius, 0, 15 * Math.PI, false);
            if (document.documentElement.getAttribute('data-bs-theme') == 'dark') {
                ctx.fillStyle = "rgba("+glyphcolordark[0]+","+glyphcolordark[1]+","+glyphcolordark[2]+"," + _this.active + ")";
            }
            else {
                ctx.fillStyle = "rgba("+glyphcolor[0]+","+glyphcolor[1]+","+glyphcolor[2]+"," + _this.active + ")";
            }
			ctx.fill();
		};
	}

	// Util
	function getDistance(p1, p2) {
		return Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2);
	}
};

jQuery(document).ready(function() {
	icBgAnimation();
});
